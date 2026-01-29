"""
使用Hyperliquid SDK下限价单，并进行正确的价格计算。
演示带市场偏移的订单下单和结果验证。
"""

import asyncio
import json
import os
from typing import Optional

from dotenv import load_dotenv
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils.signing import OrderType as HLOrderType

load_dotenv()

# 你只能在官方Hyperliquid公共API上使用此端点。
# Chainstack不可用，因为开源节点实现尚不支持它。
BASE_URL = os.getenv("HYPERLIQUID_TESTNET_PUBLIC_BASE_URL")
SYMBOL = "BTC"
ORDER_SIZE = 0.001  # 小测试大小
PRICE_OFFSET_PCT = -5  # 买单价格低于市场5%


async def method_sdk(private_key: str) -> Optional[str]:
    """方法：使用Hyperliquid Python SDK"""
    print("Method: Hyperliquid SDK")
    print("-" * 30)

    try:
        wallet = Account.from_key(private_key)
        exchange = Exchange(wallet, BASE_URL)
        info = Info(BASE_URL, skip_ws=True)

        all_prices = info.all_mids()
        market_price = float(all_prices.get(SYMBOL, 0))

        if market_price == 0:
            print(f"Could not get {SYMBOL} price")
            return None

        order_price = market_price * (1 + PRICE_OFFSET_PCT / 100)
        order_price = round(order_price, 0)

        print(f"Current {SYMBOL} price: ${market_price:,.2f}")
        print(f"Placing buy order: {ORDER_SIZE} {SYMBOL} @ ${order_price:,.2f}")

        result = exchange.order(
            name=SYMBOL,
            is_buy=True,
            sz=ORDER_SIZE,
            limit_px=order_price,
            order_type=HLOrderType({"limit": {"tif": "Gtc"}}),
            reduce_only=False,
        )

        print(f"Order result:")
        print(json.dumps(result, indent=2))

        if result and result.get("status") == "ok":
            response_data = result.get("response", {}).get("data", {})
            statuses = response_data.get("statuses", [])

            if statuses:
                status_info = statuses[0]
                if "resting" in status_info:
                    order_id = status_info["resting"]["oid"]
                    print(f"Order placed successfully! ID: {order_id}")
                    return order_id
                elif "filled" in status_info:
                    print(f"Order filled immediately!")
                    return "filled"

        print(f"Order placement unclear")
        return None

    except Exception as e:
        print(f"SDK method failed: {e}")
        return None


async def main() -> None:
    print("Hyperliquid Limit Orders")
    print("=" * 40)

    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("Set HYPERLIQUID_TESTNET_PRIVATE_KEY in your .env file")
        print("Create .env file with: HYPERLIQUID_TESTNET_PRIVATE_KEY=0x...")
        print("WARNING: This will place REAL orders on testnet!")
        return

    order_id = await method_sdk(private_key)

    if order_id:
        print("\nOrder placed successfully!")
        print("Check open orders to verify placement")


if __name__ == "__main__":
    asyncio.run(main())
