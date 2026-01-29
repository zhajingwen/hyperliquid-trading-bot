#!/usr/bin/env python3
"""
网格交易机器人启动器

简洁明了的入口点,用于运行网格交易策略。
没有混乱的命名 - 就是"run_bot.py"。
"""

import asyncio
import argparse
import sys
import os
import signal
from pathlib import Path
import yaml
from typing import Optional

# 如果存在则加载.env文件
from dotenv import load_dotenv

load_dotenv()

# 将src添加到路径以便导入
sys.path.append(str(Path(__file__).parent))

from core.engine import TradingEngine
from core.enhanced_config import EnhancedBotConfig


class GridTradingBot:
    """
    简单的网格交易机器人运行器

    简洁的接口 - 没有"增强"或"高级"的混淆。
    只是一个运行网格交易策略的机器人。
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.engine = None
        self.running = False

        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理关闭信号"""
        print(f"\n📡 Received signal {signum}, shutting down...")
        self.running = False
        if self.engine:
            asyncio.create_task(self.engine.stop())

    async def run(self) -> None:
        """运行机器人"""

        try:
            # 加载配置
            print(f"📁 Loading configuration: {self.config_path}")
            self.config = EnhancedBotConfig.from_yaml(Path(self.config_path))
            print(f"✅ Configuration loaded: {self.config.name}")

            # 转换为引擎配置格式
            engine_config = self._convert_config()

            # 初始化交易引擎
            self.engine = TradingEngine(engine_config)

            if not await self.engine.initialize():
                print("❌ Failed to initialize trading engine")
                return

            # 开始交易
            print(f"🚀 Starting {self.config.name}")
            self.running = True
            await self.engine.start()

        except KeyboardInterrupt:
            print("\n📡 Keyboard interrupt received")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if self.engine:
                await self.engine.stop()

    def _convert_config(self) -> dict:
        """将EnhancedBotConfig转换为引擎配置格式"""

        testnet = os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true"

        # 从账户余额百分比计算USD总分配
        # 注意:这是简化的方法 - 生产环境中应获取实际账户余额
        # 目前使用默认基础金额$1000 USD
        base_allocation_usd = 1000.0
        total_allocation_usd = base_allocation_usd * (
            self.config.account.max_allocation_pct / 100.0
        )

        return {
            "exchange": {
                "type": self.config.exchange.type,
                "testnet": self.config.exchange.testnet,
            },
            "strategy": {
                "type": "basic_grid",  # 默认使用基础网格
                "symbol": self.config.grid.symbol,
                "levels": self.config.grid.levels,
                "range_pct": self.config.grid.price_range.auto.range_pct,
                "total_allocation": total_allocation_usd,
                "rebalance_threshold_pct": self.config.risk_management.rebalance.price_move_threshold_pct,
            },
            "bot_config": {
                # 传递整个配置以便KeyManager可以查找机器人特定的密钥
                "name": self.config.name,
                "private_key_file": getattr(self.config, "private_key_file", None),
                "testnet_key_file": getattr(self.config, "testnet_key_file", None),
                "mainnet_key_file": getattr(self.config, "mainnet_key_file", None),
                "private_key": getattr(self.config, "private_key", None),
                "testnet_private_key": getattr(
                    self.config, "testnet_private_key", None
                ),
                "mainnet_private_key": getattr(
                    self.config, "mainnet_private_key", None
                ),
            },
            "log_level": self.config.monitoring.log_level,
        }


def find_first_active_config() -> Optional[Path]:
    """在bots文件夹中查找第一个活动配置"""

    # 相对于脚本位置查找bots文件夹
    script_dir = Path(__file__).parent
    bots_dir = script_dir.parent / "bots"

    if not bots_dir.exists():
        return None

    # 扫描YAML文件
    yaml_files = list(bots_dir.glob("*.yaml")) + list(bots_dir.glob("*.yml"))

    for yaml_file in sorted(yaml_files):
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)

            # 检查配置是否激活
            if data and data.get("active", False):
                print(f"📁 Found active config: {yaml_file.name}")
                return yaml_file

        except Exception as e:
            print(f"⚠️ Error reading {yaml_file.name}: {e}")
            continue

    return None


async def main():
    """主入口点"""
    parser = argparse.ArgumentParser(description="Grid Trading Bot")
    parser.add_argument(
        "config",
        nargs="?",
        help="配置文件路径(可选 - 如果未提供将自动发现)",
    )
    parser.add_argument(
        "--validate", action="store_true", help="仅验证配置"
    )

    args = parser.parse_args()

    # 确定配置文件
    config_path = None
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Config file not found: {args.config}")
            return 1
    else:
        # 自动发现第一个活动配置
        print("🔍 No config specified, auto-discovering active config...")
        config_path = find_first_active_config()
        if not config_path:
            print("❌ No active config found in bots/ folder")
            print("💡 Create a config file in bots/ folder with 'active: true'")
            return 1

    if args.validate:
        # 仅验证配置
        try:
            config = EnhancedBotConfig.from_yaml(config_path)
            config.validate()
            print("✅ Configuration is valid")
            return 0
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return 1

    # 运行机器人
    bot = GridTradingBot(str(config_path))
    await bot.run()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
