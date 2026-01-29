"""
用于取消特定现货订单以查看其在WebSocket中如何显示的测试脚本。
查找并取消单个未成交的现货订单。
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


async def cancel_spot_order():
    """Cancel a spot order"""
    print("Cancel Spot Order Test")
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
        print(f"📋 Found {len(open_orders)} open orders")

        if not open_orders:
            print("❌ No open orders to cancel")
            print("💡 Run place_order.py first to create an order")
            return

        # Find the first spot order
        spot_order = None
        for order in open_orders:
            coin = order.get("coin", "")
            if coin.startswith("@") or "/" in coin:  # Spot order indicators
                spot_order = order
                break

        if not spot_order:
            print("❌ No spot orders found to cancel")
            print("💡 Only perpetual orders are open")
            return

        order_id = spot_order.get("oid")
        coin_field = spot_order.get("coin")
        side = "BUY" if spot_order.get("side") == "B" else "SELL"
        size = spot_order.get("sz")
        price = spot_order.get("limitPx")

        print(f"🎯 Found spot order to cancel:")
        print(f"   ID: {order_id}")
        print(f"   Type: {side} {size} {coin_field} @ ${price}")

        # Cancel the order using correct parameter name
        print(f"🔄 Cancelling order {order_id}...")
        result = exchange.cancel(name=coin_field, oid=order_id)

        print(f"📋 Cancel result:")
        print(json.dumps(result, indent=2))

        if result and result.get("status") == "ok":
            print(f"✅ Order {order_id} cancelled successfully!")
            print(f"🔍 Monitor this cancellation in your WebSocket stream")
        else:
            print(f"❌ Cancel failed: {result}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(cancel_spot_order())
