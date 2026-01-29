"""
Hyperliquid市场数据提供者

基于WebSocket的实时市场数据实现。
技术实现与业务逻辑分离。
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable, Any
import time

from interfaces.strategy import MarketData
from core.endpoint_router import get_endpoint_router


class HyperliquidMarketData:
    """
    Hyperliquid WebSocket市场数据提供者

    通过WebSocket提供实时价格推送和市场数据。
    自动处理重连和错误恢复。
    """

    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.ws = None
        self.running = False
        self.subscribed_assets: set = set()

        # 回调函数
        self.price_callbacks: Dict[str, List[Callable[[MarketData], None]]] = {}

        # 最新数据缓存
        self.latest_data: Dict[str, MarketData] = {}

        # 连接参数
        self.reconnect_delay = 5.0
        self.max_reconnect_attempts = 10

        # 任务管理
        self.message_handler_task = None

        # 用于智能路由的端点路由器
        self.endpoint_router = get_endpoint_router(testnet)

    async def connect(self) -> bool:
        """使用公共端点连接到Hyperliquid WebSocket"""
        try:
            import websockets

            # Use direct public WebSocket endpoint
            ws_url = (
                "wss://api.hyperliquid-testnet.xyz/ws"
                if self.testnet
                else "wss://api.hyperliquid.xyz/ws"
            )

            self.ws = await websockets.connect(ws_url)
            self.running = True

            # 仅在尚未运行时启动消息处理器
            if self.message_handler_task is None or self.message_handler_task.done():
                self.message_handler_task = asyncio.create_task(self._message_handler())

            print(
                f"✅ Connected to Hyperliquid WebSocket ({'testnet' if self.testnet else 'mainnet'})"
            )
            print(f"📡 Using WebSocket: {ws_url}")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to WebSocket: {e}")
            return False

    async def disconnect(self) -> None:
        """从WebSocket断开连接"""
        self.running = False

        # 取消消息处理器任务
        if self.message_handler_task and not self.message_handler_task.done():
            self.message_handler_task.cancel()
            try:
                await self.message_handler_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()
            self.ws = None
        print("🔌 Disconnected from Hyperliquid WebSocket")

    async def subscribe_price_updates(
        self, asset: str, callback: Callable[[MarketData], None]
    ) -> None:
        """订阅资产的价格更新"""

        if asset not in self.price_callbacks:
            self.price_callbacks[asset] = []

        self.price_callbacks[asset].append(callback)
        self.subscribed_assets.add(asset)

        # 通过WebSocket订阅
        if self.ws and self.running:
            subscribe_msg = {"method": "subscribe", "subscription": {"type": "allMids"}}
            await self.ws.send(json.dumps(subscribe_msg))

        print(f"📊 Subscribed to {asset} price updates")

    async def unsubscribe_price_updates(
        self, asset: str, callback: Callable[[MarketData], None]
    ) -> None:
        """Unsubscribe from price updates"""

        if asset in self.price_callbacks:
            try:
                self.price_callbacks[asset].remove(callback)
                if not self.price_callbacks[asset]:
                    del self.price_callbacks[asset]
                    self.subscribed_assets.discard(asset)
            except ValueError:
                pass

    def get_latest_price(self, asset: str) -> Optional[float]:
        """Get latest cached price for an asset"""
        if asset in self.latest_data:
            return self.latest_data[asset].price
        return None

    def get_latest_data(self, asset: str) -> Optional[MarketData]:
        """Get latest cached market data for an asset"""
        return self.latest_data.get(asset)

    async def _message_handler(self) -> None:
        """Handle incoming WebSocket messages"""

        reconnect_attempts = 0

        while self.running:
            try:
                if not self.ws:
                    # Attempt reconnection (without calling self.connect() to avoid task recursion)
                    if reconnect_attempts < self.max_reconnect_attempts:
                        print(
                            f"🔄 Reconnecting to WebSocket (attempt {reconnect_attempts + 1})"
                        )
                        if await self._reconnect():
                            reconnect_attempts = 0
                            # Re-subscribe to assets
                            await self._resubscribe_all()
                        else:
                            reconnect_attempts += 1
                            await asyncio.sleep(self.reconnect_delay)
                            continue
                    else:
                        print("❌ Max reconnection attempts exceeded")
                        break

                # Listen for messages
                async for message in self.ws:
                    try:
                        data = json.loads(message)
                        await self._process_message(data)
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"❌ Error processing message: {e}")
                        continue

            except Exception as e:
                print(f"❌ WebSocket error: {e}")
                self.ws = None
                reconnect_attempts += 1

                if reconnect_attempts < self.max_reconnect_attempts:
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    break

    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process incoming WebSocket message"""

        # Handle different message types
        if data.get("channel") == "allMids":
            await self._handle_price_update(data.get("data", {}))

    async def _handle_price_update(self, price_data: Dict[str, Any]) -> None:
        """Handle price update message"""

        # Extract mids data (price_data structure: {"mids": {"BTC": "12345.67", "ETH": "3456.78", ...}})
        mids = price_data.get("mids", {})

        for asset, price_str in mids.items():
            if asset in self.subscribed_assets:
                try:
                    price = float(price_str)
                    timestamp = time.time()

                    # Create MarketData object
                    market_data = MarketData(
                        asset=asset,
                        price=price,
                        volume_24h=0.0,  # Not provided in allMids
                        timestamp=timestamp,
                    )

                    # Cache latest data
                    self.latest_data[asset] = market_data

                    # Notify callbacks
                    if asset in self.price_callbacks:
                        for callback in self.price_callbacks[asset]:
                            try:
                                # Check if callback is async
                                if asyncio.iscoroutinefunction(callback):
                                    asyncio.create_task(callback(market_data))
                                else:
                                    callback(market_data)
                            except Exception as e:
                                print(f"❌ Error in price callback: {e}")

                except (ValueError, TypeError) as e:
                    print(f"❌ Invalid price data for {asset}: {e}")

    async def _reconnect(self) -> bool:
        """Reconnect to WebSocket without creating new tasks"""
        try:
            import websockets

            # Use direct public WebSocket endpoint
            ws_url = (
                "wss://api.hyperliquid-testnet.xyz/ws"
                if self.testnet
                else "wss://api.hyperliquid.xyz/ws"
            )

            self.ws = await websockets.connect(ws_url)

            print(
                f"✅ Connected to Hyperliquid WebSocket ({'testnet' if self.testnet else 'mainnet'})"
            )
            print(f"📡 Using WebSocket: {ws_url}")
            return True

        except Exception as e:
            print(f"❌ Failed to reconnect to WebSocket: {e}")
            return False

    async def _resubscribe_all(self) -> None:
        """Re-subscribe to all assets after reconnection"""

        if self.subscribed_assets and self.ws and self.running:
            subscribe_msg = {"method": "subscribe", "subscription": {"type": "allMids"}}
            await self.ws.send(json.dumps(subscribe_msg))

            print(f"🔄 Re-subscribed to {len(self.subscribed_assets)} assets")

    def get_status(self) -> Dict[str, Any]:
        """Get market data provider status"""
        return {
            "connected": self.running and self.ws is not None,
            "subscribed_assets": list(self.subscribed_assets),
            "latest_data_count": len(self.latest_data),
        }
