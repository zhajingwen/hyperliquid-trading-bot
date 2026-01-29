"""
Real-time monitoring of all Hyperliquid perpetual contracts using official SDK.
Demonstrates using the hyperliquid-python-sdk's built-in WebSocket functionality.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv
from hyperliquid.info import Info

load_dotenv()

BASE_URL = os.getenv(
    "HYPERLIQUID_TESTNET_CHAINSTACK_BASE_URL",
    os.getenv("HYPERLIQUID_TESTNET_PUBLIC_BASE_URL", "https://api.hyperliquid-testnet.xyz")
)


class SDKPerpetualsMonitor:
    """Monitor all perpetual contracts using official SDK WebSocket"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.prices: Dict[str, float] = {}
        self.all_perp_symbols: list = []
        self._running = True
        self.update_count = 0
        self.info: Info = None

    def load_all_perp_symbols(self) -> None:
        """Load all perpetual contract symbols"""
        temp_info = Info(self.base_url, skip_ws=True)
        meta = temp_info.meta()

        self.all_perp_symbols = [
            asset_info["name"] for asset_info in meta["universe"]
        ]

        print(f"✅ Loaded {len(self.all_perp_symbols)} perpetual contracts")

    def handle_price_update(self, data: Any) -> None:
        """Callback for price updates from SDK WebSocket"""
        if not isinstance(data, dict):
            return

        mids = data.get("data", {}).get("mids", {})
        if not mids:
            return

        for k, price_str in mids.items():
            symbol = k.lstrip("@") if isinstance(k, str) and k.startswith("@") else k

            if symbol not in self.all_perp_symbols:
                continue

            try:
                new_price = float(price_str)
                old_price = self.prices.get(symbol)
                self.prices[symbol] = new_price
                self.update_count += 1

                if old_price is not None:
                    change = new_price - old_price
                    change_pct = (change / old_price) * 100 if old_price != 0 else 0.0
                    direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    print(f"{direction} {symbol}: ${new_price:,.2f} ({change_pct:+.2f}%)")
                else:
                    print(f"🔄 {symbol}: ${new_price:,.2f}")

            except (ValueError, TypeError):
                continue

    async def display_statistics(self) -> None:
        """Display periodic statistics every 30 seconds"""
        while self._running:
            await asyncio.sleep(30)

            if not self._running:
                break

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            active_count = len(self.prices)

            print("\n" + "=" * 60)
            print(f"📊 Statistics ({timestamp})")
            print(f"   Monitored: {len(self.all_perp_symbols)} perpetuals")
            print(f"   Updates received: {self.update_count:,}")
            print(f"   Active assets: {active_count}")
            print("=" * 60 + "\n")

    async def run(self) -> None:
        """Main run loop using SDK WebSocket"""
        print("Hyperliquid - All Perpetuals Monitor (SDK Version)")
        print("=" * 60)
        print(f"🔗 Using API: {self.base_url}")

        print("🔗 Loading all perpetual contract symbols...")
        self.load_all_perp_symbols()

        print("🔗 Initializing SDK WebSocket connection...")
        self.info = Info(self.base_url, skip_ws=False)

        subscription = {"type": "allMids"}

        print("📡 Subscribing to all perpetual contracts...")
        subscription_id = self.info.subscribe(subscription, self.handle_price_update)
        print(f"✅ Subscribed with ID: {subscription_id}")
        print(f"📡 Monitoring {len(self.all_perp_symbols)} perpetual contracts")
        print("=" * 60)

        stats_task = asyncio.create_task(self.display_statistics())

        try:
            while self._running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self._running = False
            stats_task.cancel()
            try:
                await stats_task
            except asyncio.CancelledError:
                pass

            if self.info:
                print("🔌 Disconnecting WebSocket...")
                self.info.disconnect_websocket()

            print("👋 Disconnected")


async def main():
    """Main entry point"""
    monitor = SDKPerpetualsMonitor(base_url=BASE_URL)
    await monitor.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
