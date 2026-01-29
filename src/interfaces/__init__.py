"""
扩展交易系统的接口。

这些接口为添加以下内容定义了清晰的契约：
- 新的交易策略（实现TradingStrategy）
- 新的交易所/DEX（实现ExchangeAdapter）
"""

from .strategy import TradingStrategy, TradingSignal, SignalType, MarketData, Position
from .exchange import (
    ExchangeAdapter,
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
    Balance,
    MarketInfo,
)

__all__ = [
    # 策略接口
    "TradingStrategy",
    "TradingSignal",
    "SignalType",
    "MarketData",
    "Position",
    # 交易所接口
    "ExchangeAdapter",
    "Order",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "Balance",
    "MarketInfo",
]
