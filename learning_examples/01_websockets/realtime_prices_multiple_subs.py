"""
Hyperliquid实时WebSocket监控器。

支持：
- allMids (所有资产的中间价)
- trades  (特定币种的交易打印)

设计目标是让你可以通过以下方式添加更多订阅：
1) 添加新的订阅字典
2) 为其通道注册处理器
"""

import asyncio
import json
import os
import signal
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from dotenv import load_dotenv
import websockets
from hyperliquid.info import Info

load_dotenv()


WS_URL = os.getenv("HYPERLIQUID_TESTNET_PUBLIC_WS_URL")
BASE_URL = os.getenv("HYPERLIQUID_TESTNET_CHAINSTACK_BASE_URL")

ASSETS_TO_TRACK = ["ETH"]  # 用于allMids打印
TRADES_COIN = "ETH"        # 用于trades订阅

# ---- 类型 ----

JsonDict = Dict[str, Any]
Handler = Callable[[JsonDict], Awaitable[None]]


@dataclass(frozen=True)
class Subscription:
    """表示一个WS订阅对象（内部的'subscription': {...}）。"""
    type: str
    coin: Optional[str] = None
    dex: Optional[str] = None

    def to_ws(self) -> JsonDict:
        sub: JsonDict = {"type": self.type}
        if self.coin is not None:
            sub["coin"] = self.coin
        if self.dex is not None:
            sub["dex"] = self.dex
        return sub


class HyperliquidWsClient:
    def __init__(self, ws_url: str, base_url: str) -> None:
        self.ws_url = ws_url
        self.base_url = base_url

        # 状态
        self.prices: Dict[str, float] = {}
        self.id_to_symbol: Dict[str, str] = {}

        # 调度器
        self.handlers: Dict[str, Handler] = {}

        # 停止标志
        self._running = True

    # ---- 生命周期 ----

    def stop(self) -> None:
        self._running = False

    def install_signal_handlers(self) -> None:
        def _sigint_handler(signum, frame):
            print("\nShutting down...")
            self.stop()

        signal.signal(signal.SIGINT, _sigint_handler)

    async def load_symbol_mapping(self) -> None:
        """
        使用Info.meta()加载assetId -> symbol映射。

        注意：官方allMids文档将mids描述为Record<string, string>。
        实际上你可能会看到类似"@<asset_id>"的键（你的代码处理的内容）。
        此映射让你将这些转换为符号。
        """
        info = Info(self.base_url, skip_ws=True)
        meta = info.meta()

        self.id_to_symbol.clear()
        for i, asset_info in enumerate(meta["universe"]):
            symbol = asset_info["name"]
            self.id_to_symbol[str(i)] = symbol

        print(f"Loaded {len(self.id_to_symbol)} asset mappings")

    # ---- 订阅辅助方法 ----

    async def send_subscribe(self, websocket, sub: Subscription) -> None:
        msg = {"method": "subscribe", "subscription": sub.to_ws()}
        await websocket.send(json.dumps(msg))

    async def send_unsubscribe(self, websocket, sub: Subscription) -> None:
        msg = {"method": "unsubscribe", "subscription": sub.to_ws()}
        await websocket.send(json.dumps(msg))

    # ---- 处理器注册 ----

    def on(self, channel: str, handler: Handler) -> None:
        """为给定的传入消息通道注册处理器。"""
        self.handlers[channel] = handler

    async def dispatch(self, data: JsonDict) -> None:
        channel = data.get("channel")
        if not channel:
            return
        handler = self.handlers.get(channel)
        if handler:
            await handler(data)
        else:
            # 如果你想查看其他通道，取消注释
            # print(f"ℹ️ Unhandled channel: {channel}")
            pass

    # ---- 处理器 ----

    async def handle_subscription_response(self, data: JsonDict) -> None:
        print(f"✅ Subscription confirmed: {data.get('data')}")

    async def handle_all_mids(self, data: JsonDict) -> None:
        mids = (data.get("data") or {}).get("mids") or {}
        if not isinstance(mids, dict):
            return

        for k, price_str in mids.items():
            # 键可能是"@<asset_id>"（你的原始代码假设的）,
            # 或者根据后端/版本，它们可能已经是币种符号。
            symbol: Optional[str] = None

            if isinstance(k, str) and k.startswith("@"):
                # asset_id = k.lstrip("@")
                # symbol = self.id_to_symbol.get(asset_id)
                # if symbol is None:
                #     # 此资产ID不在永续合约universe中，忽略
                #     continue  # 不要将其视为ETH
                continue
            elif isinstance(k, str):
                # 直接视为符号
                symbol = k

            if not symbol or symbol not in ASSETS_TO_TRACK:
                continue

            try:
                new_price = float(price_str)
            except (TypeError, ValueError):
                continue

            old_price = self.prices.get(symbol)
            self.prices[symbol] = new_price

            if old_price is None:
                print(f"🔄 {symbol}: ${new_price:,.2f}")
                continue

            change = new_price - old_price
            change_pct = (change / old_price) * 100 if old_price != 0 else 0.0
            direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            print(f"{direction} {symbol}: ${new_price:,.2f} ({change_pct:+.2f}%)")

    async def handle_trades(self, data: JsonDict) -> None:
        trades = data.get("data")
        if not isinstance(trades, list):
            return

        for t in trades:
            if not isinstance(t, dict):
                continue

            coin = t.get("coin")
            if coin != TRADES_COIN:
                continue

            side = t.get("side")
            px = t.get("px")
            sz = t.get("sz")
            ts = t.get("time")
            tid = t.get("tid")

            # 最小化、可读的交易打印
            print(f"🧾 TRADE {coin} {side} px={px} sz={sz} time={ts} tid={tid}")

    # ---- 主循环 ----

    async def run(self, subs: List[Subscription]) -> None:
        print("🔗 Loading asset mappings...")
        await self.load_symbol_mapping()

        print(f"🔗 Connecting to {self.ws_url}")
        self.install_signal_handlers()

        # 注册默认处理器
        self.on("subscriptionResponse", self.handle_subscription_response)
        self.on("allMids", self.handle_all_mids)
        self.on("trades", self.handle_trades)

        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("✅ WebSocket connected!")

                # 订阅所有请求的内容
                for sub in subs:
                    await self.send_subscribe(websocket, sub)

                print("📡 Subscribed to:")
                for sub in subs:
                    print(f"  - {sub.to_ws()}")
                print("=" * 60)

                async for message in websocket:
                    if not self._running:
                        break

                    try:
                        payload = json.loads(message)
                    except json.JSONDecodeError:
                        print("⚠️ Received invalid JSON")
                        continue

                    try:
                        await self.dispatch(payload)
                    except Exception as e:
                        print(f"❌ Handler error: {e}")

        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket connection closed")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
        finally:
            print("👋 Disconnected")


async def main():
    print("Hyperliquid WebSocket Monitor")
    print("=" * 60)

    if not WS_URL or not BASE_URL:
        print("❌ Missing environment variables")
        print("Set Hyperliquid endpoints in your .env file")
        return

    client = HyperliquidWsClient(ws_url=WS_URL, base_url=BASE_URL)
    # 订阅类型:
    # mids
    # allMids
    # trades
    # book
    # user
    # funding
    # liquidations
    # openOrders
    # fills
    # ohlc
    subs = [
        Subscription(type="allMids"),
        # Subscription(type="allMids", dex="xyz"),
        # Subscription(type="trades", coin=TRADES_COIN),
    ]
    # Dex列表:
    #     curl -s https://api.hyperliquid.xyz/info \
    #   -H 'Content-Type: application/json' \
    #   -d '{"type":"perpDexs"}'

    # xyz (fullName: "XYZ")
    # flx (fullName: "Felix Exchange")
    # vntl (fullName: "Ventuals")
    # hyna (fullName: "HyENA")
    await client.run(subs)


if __name__ == "__main__":
    asyncio.run(main())
