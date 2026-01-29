#!/usr/bin/env python3
"""
增强型透明配置系统

所有假设都是明确的且用户可配置的。
没有对用户隐藏的魔法数字。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Literal, Union
from enum import Enum
import yaml
from pathlib import Path


class RiskLevel(Enum):
    """具有明确参数的风险级别"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class AccountConfig:
    """账户和风险设置 - 用户控制一切"""

    max_allocation_pct: float = 20.0  # 此机器人使用的账户最大百分比
    risk_level: RiskLevel = RiskLevel.MODERATE  # 风险配置

    def validate(self) -> None:
        """验证账户配置"""
        if not 1.0 <= self.max_allocation_pct <= 100.0:
            raise ValueError("max_allocation_pct must be between 1.0 and 100.0")


@dataclass
class AutoPriceRangeConfig:
    """自动价格区间设置 - 透明假设"""

    range_pct: float = 10.0  # 距当前价格的±百分比
    volatility_adjustment: bool = True  # 高波动性时扩大区间
    min_range_pct: float = 5.0  # 低波动性下的最小区间
    max_range_pct: float = 25.0  # 高波动性下的最大区间
    volatility_multiplier: float = 2.0  # 波动性影响的乘数

    def validate(self) -> None:
        """验证自动价格区间配置"""
        if not 1.0 <= self.range_pct <= 50.0:
            raise ValueError("range_pct must be between 1.0 and 50.0")
        if not 1.0 <= self.min_range_pct <= self.max_range_pct:
            raise ValueError("min_range_pct must be <= max_range_pct")
        if self.range_pct < self.min_range_pct or self.range_pct > self.max_range_pct:
            raise ValueError(
                "range_pct must be between min_range_pct and max_range_pct"
            )


@dataclass
class ManualPriceRangeConfig:
    """手动价格区间设置"""

    min: float = 90000.0
    max: float = 120000.0

    def validate(self) -> None:
        """验证手动价格区间"""
        if self.min >= self.max:
            raise ValueError("min price must be less than max price")
        if self.min <= 0 or self.max <= 0:
            raise ValueError("prices must be positive")


@dataclass
class PriceRangeConfig:
    """具有自动/手动模式的价格区间配置"""

    mode: Literal["auto", "manual"] = "auto"
    auto: AutoPriceRangeConfig = field(default_factory=AutoPriceRangeConfig)
    manual: ManualPriceRangeConfig = field(default_factory=ManualPriceRangeConfig)

    def validate(self) -> None:
        """验证价格区间配置"""
        if self.mode not in ["auto", "manual"]:
            raise ValueError("mode must be 'auto' or 'manual'")
        self.auto.validate()
        self.manual.validate()


@dataclass
class AutoPositionSizingConfig:
    """自动仓位管理设置 - 透明假设"""

    balance_reserve_pct: float = 50.0  # 保留为储备的余额百分比
    max_single_position_pct: float = 10.0  # 单个持仓的最大百分比
    grid_spacing_strategy: Literal["percentage", "fixed"] = "percentage"
    volatility_position_adjustment: bool = True  # 对波动性资产减小仓位
    min_position_size_usd: float = 10.0  # 最小仓位大小(USD)

    def validate(self) -> None:
        """验证自动仓位管理"""
        if not 10.0 <= self.balance_reserve_pct <= 90.0:
            raise ValueError("balance_reserve_pct must be between 10.0 and 90.0")
        if not 1.0 <= self.max_single_position_pct <= 50.0:
            raise ValueError("max_single_position_pct must be between 1.0 and 50.0")
        if self.min_position_size_usd <= 0:
            raise ValueError("min_position_size_usd must be positive")


@dataclass
class ManualPositionSizingConfig:
    """手动仓位管理设置"""

    size_per_level: float = 0.0001  # 每个网格层级的资产数量

    def validate(self) -> None:
        """验证手动仓位管理"""
        if self.size_per_level <= 0:
            raise ValueError("size_per_level must be positive")


@dataclass
class PositionSizingConfig:
    """具有自动/手动模式的仓位管理配置"""

    mode: Literal["auto", "manual"] = "auto"
    auto: AutoPositionSizingConfig = field(default_factory=AutoPositionSizingConfig)
    manual: ManualPositionSizingConfig = field(
        default_factory=ManualPositionSizingConfig
    )

    def validate(self) -> None:
        """验证仓位管理配置"""
        if self.mode not in ["auto", "manual"]:
            raise ValueError("mode must be 'auto' or 'manual'")
        self.auto.validate()
        self.manual.validate()


@dataclass
class GridConfig:
    """网格配置"""

    symbol: str = "BTC"
    levels: int = 15  # 网格层级数量
    price_range: PriceRangeConfig = field(default_factory=PriceRangeConfig)
    position_sizing: PositionSizingConfig = field(default_factory=PositionSizingConfig)

    def validate(self) -> None:
        """验证网格配置"""
        if not self.symbol:
            raise ValueError("symbol cannot be empty")
        if not 3 <= self.levels <= 50:
            raise ValueError("levels must be between 3 and 50")
        self.price_range.validate()
        self.position_sizing.validate()


@dataclass
class RebalanceConfig:
    """再平衡触发设置"""

    price_move_threshold_pct: float = 15.0  # 价格移动超出区间百分比时再平衡
    time_based: bool = False  # 不基于时间进行再平衡
    cooldown_minutes: int = 30  # 再平衡之间等待的分钟数
    max_rebalances_per_day: int = 10  # 限制再平衡频率

    def validate(self) -> None:
        """验证再平衡配置"""
        if not 5.0 <= self.price_move_threshold_pct <= 50.0:
            raise ValueError("price_move_threshold_pct must be between 5.0 and 50.0")
        if self.cooldown_minutes < 1:
            raise ValueError("cooldown_minutes must be at least 1")
        if self.max_rebalances_per_day < 1:
            raise ValueError("max_rebalances_per_day must be at least 1")


@dataclass
class RiskManagementConfig:
    """风险管理设置 - 所有假设都可见"""

    max_drawdown_pct: float = 15.0  # 回撤百分比时停止
    max_position_size_pct: float = 30.0  # 资产持有永不超过此百分比
    stop_loss_enabled: bool = False  # 启用止损
    stop_loss_pct: float = 5.0  # 止损百分比
    take_profit_enabled: bool = False  # 启用止盈
    take_profit_pct: float = 20.0  # 止盈百分比
    rebalance: RebalanceConfig = field(default_factory=RebalanceConfig)

    def validate(self) -> None:
        """验证风险管理配置"""
        if not 5.0 <= self.max_drawdown_pct <= 50.0:
            raise ValueError("max_drawdown_pct must be between 5.0 and 50.0")
        if not 10.0 <= self.max_position_size_pct <= 100.0:
            raise ValueError("max_position_size_pct must be between 10.0 and 100.0")
        if self.stop_loss_enabled and not 1.0 <= self.stop_loss_pct <= 20.0:
            raise ValueError("stop_loss_pct must be between 1.0 and 20.0")
        if self.take_profit_enabled and not 5.0 <= self.take_profit_pct <= 100.0:
            raise ValueError("take_profit_pct must be between 5.0 and 100.0")
        self.rebalance.validate()


@dataclass
class MarketDataConfig:
    """市场数据设置"""

    volatility_window_hours: int = 24  # 计算波动性的小时数
    connection_retry_attempts: int = 3  # 连接重试次数
    connection_timeout_sec: int = 10  # 连接超时
    websocket_reconnect_delay_sec: float = 5.0  # WebSocket重连前的延迟

    def validate(self) -> None:
        """验证市场数据配置"""
        if not 1 <= self.volatility_window_hours <= 168:  # 最多1周
            raise ValueError("volatility_window_hours must be between 1 and 168")


@dataclass
class ExchangeConfig:
    """交易所配置设置"""

    type: str = "hyperliquid"  # 交易所类型(hyperliquid, hl等)
    testnet: bool = True  # 使用测试网进行开发

    def validate(self) -> None:
        """验证交易所配置"""
        if not self.type:
            raise ValueError("exchange type cannot be empty")


@dataclass
class MonitoringConfig:
    """日志和监控设置"""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    report_interval_minutes: int = 60  # 状态报告间隔
    save_trade_history: bool = True  # 将交易历史保存到文件
    metrics_export: bool = False  # 导出指标用于监控

    def validate(self) -> None:
        """验证监控配置"""
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError("log_level must be DEBUG, INFO, WARNING, or ERROR")
        if self.report_interval_minutes < 1:
            raise ValueError("report_interval_minutes must be at least 1")


@dataclass
class EnhancedBotConfig:
    """完整的增强型机器人配置,所有假设都明确"""

    name: str
    active: bool = True
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    account: AccountConfig = field(default_factory=AccountConfig)
    grid: GridConfig = field(default_factory=GridConfig)
    risk_management: RiskManagementConfig = field(default_factory=RiskManagementConfig)
    market_data: MarketDataConfig = field(default_factory=MarketDataConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # 可选的机器人特定私钥配置(覆盖环境密钥)
    private_key: Optional[str] = None  # 两个环境的单一密钥
    testnet_private_key: Optional[str] = None  # 测试网特定密钥
    mainnet_private_key: Optional[str] = None  # 主网特定密钥
    private_key_file: Optional[str] = None  # 单一密钥文件路径
    testnet_key_file: Optional[str] = None  # 测试网密钥文件路径
    mainnet_key_file: Optional[str] = None  # 主网密钥文件路径

    def validate(self) -> None:
        """验证整个配置"""
        if not self.name:
            raise ValueError("Bot name cannot be empty")

        # 验证所有部分
        self.exchange.validate()
        self.account.validate()
        self.grid.validate()
        self.risk_management.validate()
        self.market_data.validate()
        self.monitoring.validate()

        # 交叉验证检查
        if isinstance(self.account.risk_level, str):
            self.account.risk_level = RiskLevel(self.account.risk_level)

        # 确保资金分配与风险管理一致
        if self.account.max_allocation_pct > (
            100.0 - self.grid.position_sizing.auto.balance_reserve_pct
        ):
            raise ValueError(
                f"max_allocation_pct ({self.account.max_allocation_pct}%) conflicts with "
                f"balance_reserve_pct ({self.grid.position_sizing.auto.balance_reserve_pct}%)"
            )

        # 验证私钥配置(安全检查)
        self._validate_private_keys()

    def _validate_private_keys(self) -> None:
        """验证私钥配置并发出安全警告"""
        import logging

        logger = logging.getLogger(__name__)

        # 检查配置中直接包含的密钥(不推荐)
        direct_keys = [
            self.private_key,
            self.testnet_private_key,
            self.mainnet_private_key,
        ]
        if any(key is not None for key in direct_keys):
            logger.warning(
                "⚠️  SECURITY WARNING: Private keys found directly in config file!"
            )
            logger.warning(
                "⚠️  Consider using key files or environment variables instead"
            )

        # 如果指定则验证密钥文件路径
        key_files = [
            self.private_key_file,
            self.testnet_key_file,
            self.mainnet_key_file,
        ]
        for key_file in key_files:
            if key_file is not None:
                key_path = Path(key_file)
                if not key_path.is_absolute():
                    # 将相对路径转换为相对于配置目录的路径
                    continue
                if not key_path.exists():
                    logger.warning(f"⚠️  Key file not found: {key_file}")

        # 如果直接提供则验证密钥格式
        for key_name, key_value in [
            ("private_key", self.private_key),
            ("testnet_private_key", self.testnet_private_key),
            ("mainnet_private_key", self.mainnet_private_key),
        ]:
            if key_value is not None:
                if not isinstance(key_value, str):
                    raise ValueError(f"{key_name} must be a string")
                if not (key_value.startswith("0x") and len(key_value) == 66):
                    if not (len(key_value) == 64):  # 允许没有0x前缀
                        logger.warning(
                            f"⚠️  {key_name} may have invalid format (should be 64 hex chars or 0x + 64 hex chars)"
                        )

    @classmethod
    def from_yaml(cls, file_path: Union[str, Path]) -> "EnhancedBotConfig":
        """从YAML文件加载配置"""
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        # 将嵌套字典转换为数据类
        config = cls._dict_to_dataclass(data)
        config.validate()
        return config

    @classmethod
    def _dict_to_dataclass(cls, data: Dict[str, Any]) -> "EnhancedBotConfig":
        """递归地将字典转换为数据类"""
        # 处理嵌套结构
        if "exchange" in data:
            data["exchange"] = ExchangeConfig(**data["exchange"])

        if "account" in data:
            data["account"] = AccountConfig(**data["account"])

        if "grid" in data:
            grid_data = data["grid"]
            if "price_range" in grid_data:
                pr_data = grid_data["price_range"]
                if "auto" in pr_data:
                    pr_data["auto"] = AutoPriceRangeConfig(**pr_data["auto"])
                if "manual" in pr_data:
                    pr_data["manual"] = ManualPriceRangeConfig(**pr_data["manual"])
                grid_data["price_range"] = PriceRangeConfig(**pr_data)

            if "position_sizing" in grid_data:
                ps_data = grid_data["position_sizing"]
                if "auto" in ps_data:
                    ps_data["auto"] = AutoPositionSizingConfig(**ps_data["auto"])
                if "manual" in ps_data:
                    ps_data["manual"] = ManualPositionSizingConfig(**ps_data["manual"])
                grid_data["position_sizing"] = PositionSizingConfig(**ps_data)

            data["grid"] = GridConfig(**grid_data)

        if "risk_management" in data:
            rm_data = data["risk_management"]
            if "rebalance" in rm_data:
                rm_data["rebalance"] = RebalanceConfig(**rm_data["rebalance"])
            data["risk_management"] = RiskManagementConfig(**rm_data)

        if "market_data" in data:
            data["market_data"] = MarketDataConfig(**data["market_data"])

        if "monitoring" in data:
            data["monitoring"] = MonitoringConfig(**data["monitoring"])

        return cls(**data)

    def to_yaml(self, file_path: Union[str, Path]) -> None:
        """将配置保存到YAML文件"""
        data = self._dataclass_to_dict()

        with open(file_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, indent=2, sort_keys=False)

    def _dataclass_to_dict(self) -> Dict[str, Any]:
        """递归地将数据类转换为字典"""
        seen = set()

        def convert_value(value, path=""):
            # 处理基本类型
            if value is None or isinstance(value, (str, int, float, bool)):
                return value

            # 处理枚举
            if isinstance(value, Enum):
                return value.value

            # 处理列表和元组
            if isinstance(value, (list, tuple)):
                return [
                    convert_value(item, f"{path}[{i}]") for i, item in enumerate(value)
                ]

            # 处理字典
            if isinstance(value, dict):
                return {k: convert_value(v, f"{path}.{k}") for k, v in value.items()}

            # 处理具有__dict__的对象
            if hasattr(value, "__dict__"):
                # 检查循环引用
                obj_id = id(value)
                if obj_id in seen:
                    return f"<circular reference: {type(value).__name__}>"

                seen.add(obj_id)
                try:
                    result = {
                        k: convert_value(v, f"{path}.{k}")
                        for k, v in value.__dict__.items()
                    }
                finally:
                    seen.remove(obj_id)

                return result

            # 对于其他类型,尝试转换为字符串
            return str(value)

        return {k: convert_value(v, k) for k, v in self.__dict__.items()}


def create_default_config(
    name: str, symbol: str, risk_level: RiskLevel = RiskLevel.MODERATE
) -> EnhancedBotConfig:
    """创建具有合理设置的默认配置"""

    # 根据风险级别调整设置
    if risk_level == RiskLevel.CONSERVATIVE:
        account_config = AccountConfig(max_allocation_pct=10.0, risk_level=risk_level)
        auto_price_range = AutoPriceRangeConfig(
            range_pct=5.0, min_range_pct=3.0, max_range_pct=10.0
        )
        auto_position_sizing = AutoPositionSizingConfig(
            balance_reserve_pct=70.0, max_single_position_pct=5.0
        )
        risk_management = RiskManagementConfig(
            max_drawdown_pct=10.0, max_position_size_pct=20.0
        )

    elif risk_level == RiskLevel.MODERATE:
        account_config = AccountConfig(max_allocation_pct=20.0, risk_level=risk_level)
        auto_price_range = AutoPriceRangeConfig(
            range_pct=10.0, min_range_pct=5.0, max_range_pct=20.0
        )
        auto_position_sizing = AutoPositionSizingConfig(
            balance_reserve_pct=50.0, max_single_position_pct=10.0
        )
        risk_management = RiskManagementConfig(
            max_drawdown_pct=15.0, max_position_size_pct=30.0
        )

    else:  # AGGRESSIVE
        account_config = AccountConfig(max_allocation_pct=40.0, risk_level=risk_level)
        auto_price_range = AutoPriceRangeConfig(
            range_pct=15.0, min_range_pct=10.0, max_range_pct=30.0
        )
        auto_position_sizing = AutoPositionSizingConfig(
            balance_reserve_pct=30.0, max_single_position_pct=20.0
        )
        risk_management = RiskManagementConfig(
            max_drawdown_pct=25.0, max_position_size_pct=50.0
        )

    return EnhancedBotConfig(
        name=name,
        account=account_config,
        grid=GridConfig(
            symbol=symbol,
            price_range=PriceRangeConfig(auto=auto_price_range),
            position_sizing=PositionSizingConfig(auto=auto_position_sizing),
        ),
        risk_management=risk_management,
    )
