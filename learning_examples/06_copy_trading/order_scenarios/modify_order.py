"""
用于修改现货订单以查看其在WebSocket中如何显示的测试脚本。
查找未成交的现货订单并修改其价格或大小。
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils.signing import ModifyRequest

load_dotenv()

BASE_URL = os.getenv("HYPERLIQUID_TESTNET_PUBLIC_BASE_URL")


async def modify_spot_order():
    """Modify a spot order"""
    print("Modify Spot Order Test")
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
            print("❌ No open orders to modify")
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
            print("❌ No spot orders found to modify")
            print("💡 Only perpetual orders are open")
            return

        order_id = spot_order.get("oid")
        coin_field = spot_order.get("coin")
        side = "BUY" if spot_order.get("side") == "B" else "SELL"
        current_size = float(spot_order.get("sz", 0))
        current_price = float(spot_order.get("limitPx", 0))

        print(f"🎯 Found spot order to modify:")
        print(f"   ID: {order_id}")
        print(f"   Current: {side} {current_size} {coin_field} @ ${current_price}")

        # Calculate new values
        price_modifier = (
            0.9 if side == "BUY" else 1.1
        )  # Make buy orders cheaper, sell orders more expensive
        new_price = round(current_price * price_modifier, 6)

        print(f"   New: {side} {current_size} {coin_field} @ ${new_price}")

        # Create modify request
        print(f"🔄 Modifying order {order_id}...")
        result = exchange.modify_order(
            oid=order_id,
            name=coin_field,
            is_buy=(side == "BUY"),
            sz=current_size,
            limit_px=new_price,
            order_type={"limit": {"tif": "Gtc"}},
            reduce_only=False,
        )

        print(f"📋 Modify result:")
        print(json.dumps(result, indent=2))

        if result and result.get("status") == "ok":
            print(f"✅ Order {order_id} modified successfully!")
            print(f"🔍 Monitor this modification in your WebSocket stream")
        else:
            print(f"❌ Modify failed: {result}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(modify_spot_order())
