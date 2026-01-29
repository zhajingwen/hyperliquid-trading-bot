"""
用于批量取消多个现货订单以查看其在WebSocket中如何显示的测试脚本。
使用bulk_cancel方法取消所有未成交的现货订单。
"""

import asyncio
import os
from dotenv import load_dotenv
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

load_dotenv()

BASE_URL = os.getenv("HYPERLIQUID_TESTNET_PUBLIC_BASE_URL")


async def cancel_multiple_spot_orders():
    """Cancel multiple spot orders using bulk_cancel"""
    print("Cancel Multiple Spot Orders Test")
    print("=" * 40)

    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Missing HYPERLIQUID_TESTNET_PRIVATE_KEY in .env file")
        return

    try:
        wallet = Account.from_key(private_key)
        exchange = Exchange(wallet, BASE_URL)
        info = Info(BASE_URL, skip_ws=True)

        print(f"📱 Wallet: {wallet.address}")

        # Get open orders using environment wallet address
        wallet_address = os.getenv("TESTNET_WALLET_ADDRESS") or wallet.address
        open_orders = info.open_orders(wallet_address)
        print(f"📋 Found {len(open_orders)} total open orders")

        if not open_orders:
            print("❌ No open orders to cancel")
            print("💡 Run place_order.py multiple times to create orders")
            return

        # Find all spot orders
        spot_orders = []
        for order in open_orders:
            coin = order.get("coin", "")
            if coin.startswith("@") or "/" in coin:  # Spot order indicators
                spot_orders.append(order)

        if not spot_orders:
            print("❌ No spot orders found to cancel")
            print("💡 Only perpetual orders are open")
            return

        print(f"🎯 Found {len(spot_orders)} spot orders to cancel:")

        # Cancel each order individually
        successful_cancels = 0
        failed_cancels = 0

        for order in spot_orders:
            order_id = order.get("oid")
            coin_field = order.get("coin")
            side = "BUY" if order.get("side") == "B" else "SELL"
            size = order.get("sz")
            price = order.get("limitPx")

            print(f"   Cancelling ID {order_id}: {side} {size} {coin_field} @ ${price}")

            try:
                result = exchange.cancel(name=coin_field, oid=order_id)

                if result and result.get("status") == "ok":
                    print(f"   ✅ Order {order_id} cancelled successfully")
                    successful_cancels += 1
                else:
                    print(f"   ❌ Order {order_id} cancel failed: {result}")
                    failed_cancels += 1
            except Exception as e:
                print(f"   ❌ Order {order_id} cancel error: {e}")
                failed_cancels += 1

        print(f"📋 Cancel Summary:")
        print(f"   ✅ Successful: {successful_cancels}")
        print(f"   ❌ Failed: {failed_cancels}")
        print(f"🔍 Monitor these cancellations in your WebSocket stream")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(cancel_multiple_spot_orders())
