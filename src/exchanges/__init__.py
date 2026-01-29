"""
交易所集成

不同交易所/DEX的技术实现。
通过实现ExchangeAdapter接口添加新交易所。

添加新交易所的步骤：
1. 实现ExchangeAdapter接口
2. 添加到EXCHANGE_REGISTRY
3. 更新配置以使用交易所类型
"""

from .hyperliquid import HyperliquidAdapter, HyperliquidMarketData

# 交易所注册表 - 便于添加新DEX
EXCHANGE_REGISTRY = {
    "hyperliquid": HyperliquidAdapter,
}

# 便捷别名
EXCHANGE_REGISTRY["hl"] = HyperliquidAdapter


def create_exchange_adapter(exchange_type: str, config: dict):
    """
    创建交易所适配器的工厂函数。

    便于添加新交易所：
    1. 实现ExchangeAdapter接口
    2. 添加到EXCHANGE_REGISTRY
    3. 完成！

    Args:
        exchange_type: 交易所类型（例如，"hyperliquid"，"binance"）
        config: 交易所配置字典

    Returns:
        ExchangeAdapter实例
    """
    if exchange_type not in EXCHANGE_REGISTRY:
        available = ", ".join(EXCHANGE_REGISTRY.keys())
        raise ValueError(
            f"Unknown exchange type: {exchange_type}. Available: {available}"
        )

    exchange_class = EXCHANGE_REGISTRY[exchange_type]

    # 提取交易所初始化的公共参数
    if exchange_type in ["hyperliquid", "hl"]:
        # Hyperliquid特定初始化
        private_key = config.get("private_key")
        testnet = config.get("testnet", True)

        if not private_key:
            raise ValueError("private_key is required for Hyperliquid")

        return exchange_class(private_key, testnet)

    # 未来的交易所将在此处有自己的初始化逻辑
    # elif exchange_type == "binance":
    #     api_key = config.get("api_key")
    #     secret_key = config.get("secret_key")
    #     return exchange_class(api_key, secret_key)

    else:
        # 默认：尝试直接传递配置
        return exchange_class(config)


__all__ = [
    "HyperliquidAdapter",
    "HyperliquidMarketData",
    "EXCHANGE_REGISTRY",
    "create_exchange_adapter",
]
