"""
交易策略

不同交易策略的业务逻辑。
通过实现TradingStrategy接口添加新策略。

可用策略：
- BasicGridStrategy：具有几何间距和再平衡的网格交易
"""

from .grid import BasicGridStrategy

# 策略注册表 - 便于添加新策略
STRATEGY_REGISTRY = {
    "basic_grid": BasicGridStrategy,
    "grid": BasicGridStrategy,  # 别名
}


def create_strategy(strategy_type: str, config: dict):
    """
    创建策略的工厂函数。

    便于新手添加新策略：
    1. 实现TradingStrategy接口
    2. 添加到STRATEGY_REGISTRY
    3. 完成！
    """
    if strategy_type not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unknown strategy type: {strategy_type}. Available: {available}"
        )

    strategy_class = STRATEGY_REGISTRY[strategy_type]
    return strategy_class(config)


__all__ = ["BasicGridStrategy", "STRATEGY_REGISTRY", "create_strategy"]
