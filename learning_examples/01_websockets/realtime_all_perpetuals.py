"""
Real-time monitoring of all Hyperliquid perpetual contracts.
Subscribes to all active perpetual assets and displays live price updates.
"""

import asyncio
import json
import os
import signal
from datetime import datetime
from typing import Dict, Optional

from dotenv import load_dotenv
import websockets
from hyperliquid.info import Info

load_dotenv()

WS_URL = os.getenv(
    "HYPERLIQUID_TESTNET_PUBLIC_WS_URL",
    "wss://api.hyperliquid-testnet.xyz/ws"
)
BASE_URL = os.getenv(
    "HYPERLIQUID_TESTNET_CHAINSTACK_BASE_URL",
    os.getenv("HYPERLIQUID_TESTNET_PUBLIC_BASE_URL", "https://api.hyperliquid-testnet.xyz")
)


class AllPerpetualsMonitor:
    """Monitor all perpetual contracts in real-time"""

    def __init__(self, ws_url: str, base_url: str):
        self.ws_url = ws_url
        self.base_url = base_url
        self.prices: Dict[str, float] = {}
        self.all_perp_symbols: list = []
        self._running = True
        self.update_count = 0

    async def load_all_perp_symbols(self) -> None:
        """Load all perpetual contract symbols from Hyperliquid API"""
        info = Info(self.base_url, skip_ws=True)
        meta = info.meta()

        self.all_perp_symbols = [
            asset_info["name"] for asset_info in meta["universe"]
        ]

        print(f"✅ Loaded {len(self.all_perp_symbols)} perpetual contracts")

    async def handle_price_update(self, data: dict) -> None:
        """Process price updates for all perpetual contracts"""
        mids = (data.get("data") or {}).get("mids") or {}

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

            except (ValueError, TypeError) as e:
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
        """Main run loop for the monitor"""
        print("Hyperliquid - All Perpetuals Monitor")
        print("=" * 60)
        print(f"🔗 Using WebSocket: {self.ws_url}")
        print(f"🔗 Using API: {self.base_url}")

        print("🔗 Loading all perpetual contract symbols...")
        await self.load_all_perp_symbols()

        print(f"🔗 Connecting to {self.ws_url}")

        signal.signal(signal.SIGINT, lambda s, f: self._shutdown())

        stats_task = asyncio.create_task(self.display_statistics())

        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("✅ WebSocket connected!")

                subscribe_msg = {"method": "subscribe", "subscription": {"type": "allMids"}}
                await websocket.send(json.dumps(subscribe_msg))

                print(f"📡 Monitoring {len(self.all_perp_symbols)} perpetual contracts")
                print("=" * 60)

                async for message in websocket:
                    if not self._running:
                        break

                    try:
                        data = json.loads(message)
                        if data.get("channel") == "allMids":
                            await self.handle_price_update(data)
                        elif data.get("channel") == "subscriptionResponse":
                            print("✅ Subscription confirmed")
                    except json.JSONDecodeError:
                        print("⚠️ Received invalid JSON")
                    except Exception as e:
                        print(f"❌ Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket connection closed")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
        finally:
            self._running = False
            stats_task.cancel()
            try:
                await stats_task
            except asyncio.CancelledError:
                pass
            print("👋 Disconnected")

    def _shutdown(self):
        """Handle graceful shutdown"""
        print("\n🛑 Shutting down...")
        self._running = False


async def main():
    """Main entry point"""
    monitor = AllPerpetualsMonitor(ws_url=WS_URL, base_url=BASE_URL)
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
