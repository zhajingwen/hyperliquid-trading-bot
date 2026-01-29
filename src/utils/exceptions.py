class TradingFrameworkError(Exception):
    """交易框架的基础异常"""

    pass


class ConfigurationError(TradingFrameworkError):
    """配置无效时抛出"""

    pass


class StrategyError(TradingFrameworkError):
    """策略遇到错误时抛出"""

    pass


class ExchangeError(TradingFrameworkError):
    """交易所操作失败时抛出"""

    pass


class OrderError(TradingFrameworkError):
    """订单操作失败时抛出"""

    pass


class PositionError(TradingFrameworkError):
    """持仓操作失败时抛出"""

    pass


class GridError(TradingFrameworkError):
    """网格交易操作失败时抛出"""

    pass


class TradingError(TradingFrameworkError):
    """一般交易操作错误时抛出"""

    pass
