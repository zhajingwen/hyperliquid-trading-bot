"""
演示订单取消策略：单个订单和按资产批量取消。
展示正确的订单生命周期管理和取消验证。
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

load_dotenv()

BASE_URL = os.getenv("HYPERLIQUID_TESTNET_PUBLIC_BASE_URL")
WALLET_ADDRESS = os.getenv("TESTNET_WALLET_ADDRESS")


async def method_cancel_single_order(private_key: str) -> None:
    """方法：使用SDK取消单个订单"""
    print("Method: Cancel Single Order")
    print("-" * 30)

    try:
        account = Account.from_key(private_key)
        exchange = Exchange(account, BASE_URL)
        info = Info(BASE_URL, skip_ws=True)

        open_orders = info.open_orders(WALLET_ADDRESS)

        if not open_orders:
            print("No open orders to cancel")
            return

        print(f"Found {len(open_orders)} open orders")

        for i, order in enumerate(open_orders, 1):
            oid = order.get("oid", "")
            coin = order.get("coin", "")
            side = "BUY" if order.get("side") == "B" else "SELL"
            size = order.get("sz", "0")
            price = float(order.get("limitPx", 0))

            print(f"   {i}. Order {oid}: {side} {size} {coin} @ ${price:,.2f}")

        if open_orders:
            first_order = open_orders[0]
            order_id = first_order.get("oid")

            print(f"\nCancelling order {order_id}...")
            print(f"Order details: coin={first_order.get('coin')}, oid={order_id}")

            result = exchange.cancel(
                name=first_order.get("coin", ""), oid=int(order_id)
            )

            print(f"Cancel result type: {type(result)}")
            print(f"Cancel result:")
            print(json.dumps(result, indent=2))

            # 检查结果结构
            if result and isinstance(result, dict):
                if result.get("status") == "ok":
                    response_data = result.get("response", {}).get("data", {})
                    statuses = response_data.get("statuses", [])

                    if statuses and statuses[0] == "success":
                        print(f"✅ Order {order_id} cancelled successfully!")

                        # 验证取消
                        await asyncio.sleep(2)
                        new_orders = info.open_orders(account.address)

                        still_exists = any(o.get("oid") == order_id for o in new_orders)
                        if not still_exists:
                            print(f"✅ Cancellation confirmed - order removed")
                        else:
                            print(f"⚠️  Order still appears (may take time to update)")
                    else:
                        print(f"❌ Cancel failed with status: {statuses}")
                else:
                    print(f"❌ Cancel request failed: {result}")
            else:
                print(f"❌ Unexpected response format: {result}")

    except Exception as e:
        print(f"❌ SDK method failed: {e}")


async def main() -> None:
    print("Hyperliquid Order Cancellation")
    print("=" * 40)

    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("Set HYPERLIQUID_TESTNET_PRIVATE_KEY in your .env file")
        print("Create .env file with: HYPERLIQUID_TESTNET_PRIVATE_KEY=0x...")
        print("WARNING: This will cancel REAL orders on testnet!")
        return

    await method_cancel_single_order(private_key)


if __name__ == "__main__":
    asyncio.run(main())
