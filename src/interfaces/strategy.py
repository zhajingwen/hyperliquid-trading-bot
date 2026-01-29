"""
策略接口

用于实现交易策略的简单接口。
新手可以通过实现此接口来添加新策略。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """交易信号类型"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


@dataclass
class TradingSignal:
    """来自策略的交易信号"""

    signal_type: SignalType
    asset: str
    size: float
    price: Optional[float] = None  # None = 市价单
    reason: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MarketData:
    """提供给策略的市场数据"""

    asset: str
    price: float
    volume_24h: float
    timestamp: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volatility: Optional[float] = None


@dataclass
class Position:
    """当前持仓信息"""

    asset: str
    size: float  # 正数 = 多头, 负数 = 空头
    entry_price: float
    current_value: float
    unrealized_pnl: float
    timestamp: float


class TradingStrategy(ABC):
    """
    所有交易策略的基础接口。

    这是新手添加新策略需要理解的唯一类。

    示例实现:

    class MyStrategy(TradingStrategy):
        def __init__(self, config):
            super().__init__("my_strategy", config)

        def generate_signals(self, market_data, positions, balance):
            if market_data.price < 50000:
                return [TradingSignal(SignalType.BUY, "BTC", 0.001, reason="Price dip")]
            return []
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_active = True

    @abstractmethod
    def generate_signals(
        self, market_data: MarketData, positions: List[Position], balance: float
    ) -> List[TradingSignal]:
        """
        Generate trading signals based on market data and current positions.

        Args:
            market_data: Latest market data for the asset
            positions: Current positions
            balance: Available balance

        Returns:
            List of trading signals (can be empty)
        """
        pass

    def on_trade_executed(
        self, signal: TradingSignal, executed_price: float, executed_size: float
    ) -> None:
        """
        Called when a signal results in a trade execution.
        Override to implement custom logic (e.g., tracking, logging).
        """
        pass

    def on_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Called when an error occurs in strategy execution.
        Override to implement custom error handling.
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """
        Get strategy status and metrics.
        Override to provide strategy-specific information.
        """
        return {"name": self.name, "active": self.is_active, "config": self.config}

    def start(self) -> None:
        """Called when strategy starts. Override for setup logic."""
        self.is_active = True

    def stop(self) -> None:
        """Called when strategy stops. Override for cleanup logic."""
        self.is_active = False

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update strategy configuration. Override for custom logic."""
        self.config.update(new_config)
