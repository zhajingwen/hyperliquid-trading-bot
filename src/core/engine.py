"""
交易引擎

连接策略、交易所和基础设施的主要编排组件。
简洁、专注的职责 - 没有像"增强"或"高级"这样令人困惑的命名。
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
import logging

from interfaces.strategy import (
    TradingStrategy,
    TradingSignal,
    SignalType,
    MarketData,
    Position,
)
from interfaces.exchange import (
    ExchangeAdapter,
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
)
from exchanges.hyperliquid import HyperliquidMarketData
from core.key_manager import key_manager
from core.risk_manager import RiskManager, RiskEvent, RiskAction, AccountMetrics


class TradingEngine:
    """
    编排一切的主交易引擎

    职责:
    - 将策略连接到市场数据
    - 通过交易所适配器执行交易信号
    - 管理订单生命周期
    - 协调所有组件之间的交互

    这是主"机器人" - 简洁且专注。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False

        # 核心组件
        self.strategy: Optional[TradingStrategy] = None
        self.exchange: Optional[ExchangeAdapter] = None
        self.market_data: Optional[HyperliquidMarketData] = None
        self.risk_manager: Optional[RiskManager] = None

        # 状态跟踪
        self.current_positions: List[Position] = []
        self.pending_orders: Dict[str, Order] = {}
        self.executed_trades = 0
        self.total_pnl = 0.0

        # 设置日志
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=getattr(logging, config.get("log_level", "INFO")),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def initialize(self) -> bool:
        """初始化所有组件"""

        try:
            self.logger.info("🚀 Initializing trading engine")

            # 初始化交易所适配器
            if not await self._initialize_exchange():
                return False

            # 初始化市场数据
            if not await self._initialize_market_data():
                return False

            # 初始化策略
            if not self._initialize_strategy():
                return False

            # 初始化风险管理器
            if not self._initialize_risk_manager():
                return False

            self.logger.info("✅ Trading engine initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize trading engine: {e}")
            return False

    async def _initialize_exchange(self) -> bool:
        """初始化交易所适配器"""

        exchange_config = self.config.get("exchange", {})
        testnet = exchange_config.get("testnet", True)

        try:
            # 使用KeyManager获取私钥
            bot_config = self.config.get("bot_config")  # 可选的机器人特定配置
            private_key = key_manager.get_private_key(testnet, bot_config)
        except ValueError as e:
            self.logger.error(f"❌ {e}")
            return False

        # 使用工厂模式创建交易所适配器
        from exchanges import create_exchange_adapter

        exchange_type = exchange_config.get("type", "hyperliquid")
        exchange_config_with_key = {**exchange_config, "private_key": private_key}
        self.exchange = create_exchange_adapter(exchange_type, exchange_config_with_key)

        if await self.exchange.connect():
            self.logger.info("✅ Exchange adapter connected")
            return True
        else:
            self.logger.error("❌ Failed to connect to exchange")
            return False

    async def _initialize_market_data(self) -> bool:
        """初始化市场数据提供者"""

        testnet = self.config.get("exchange", {}).get("testnet", True)
        self.market_data = HyperliquidMarketData(testnet)

        if await self.market_data.connect():
            self.logger.info("✅ Market data provider connected")
            return True
        else:
            self.logger.error("❌ Failed to connect to market data")
            return False

    def _initialize_strategy(self) -> bool:
        """初始化交易策略"""

        strategy_config = self.config.get("strategy", {})
        strategy_type = strategy_config.get("type", "basic_grid")

        try:
            from strategies import create_strategy

            self.strategy = create_strategy(strategy_type, strategy_config)

            self.strategy.start()
            self.logger.info(f"✅ Strategy initialized: {strategy_type}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize strategy: {e}")
            return False

    def _initialize_risk_manager(self) -> bool:
        """初始化风险管理器"""

        try:
            self.risk_manager = RiskManager(self.config)
            self.logger.info("✅ Risk manager initialized")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize risk manager: {e}")
            return False

    async def start(self) -> None:
        """启动交易引擎"""

        if not self.strategy or not self.exchange or not self.market_data:
            raise RuntimeError("Engine not initialized")

        self.running = True
        self.logger.info("🎬 Trading engine started")

        # 订阅策略资产的市场数据
        asset = self.config.get("strategy", {}).get("symbol", "BTC")
        await self.market_data.subscribe_price_updates(asset, self._handle_price_update)

        # 主交易循环
        await self._trading_loop()

    async def stop(self) -> None:
        """优雅地停止交易引擎"""

        self.running = False
        self.logger.info("🛑 Stopping trading engine")

        # 停止策略
        if self.strategy:
            self.strategy.stop()

        # 处理持仓和订单清理
        if self.exchange:
            try:
                # 关闭前获取当前持仓
                current_positions = await self.exchange.get_positions()

                if current_positions:
                    self.logger.info(
                        f"📊 Found {len(current_positions)} open positions"
                    )

                    # 选项1: 关闭所有持仓(更激进)
                    # for pos in current_positions:
                    #     await self.exchange.close_position(pos.asset)
                    #     self.logger.info(f"✅ Closed position: {pos.asset}")

                    # 选项2: 仅取消订单保留持仓(更保守)
                    self.logger.info(
                        "⚠️ Leaving positions open - only cancelling orders"
                    )

                # 取消所有待处理订单
                cancelled_orders = await self.exchange.cancel_all_orders()
                if cancelled_orders > 0:
                    self.logger.info(f"✅ Cancelled {cancelled_orders} pending orders")

            except Exception as e:
                self.logger.error(f"❌ Error during cleanup: {e}")

        # 断开组件连接
        if self.market_data:
            await self.market_data.disconnect()
        if self.exchange:
            await self.exchange.disconnect()

        self.logger.info("✅ Trading engine stopped")

    async def _handle_price_update(self, market_data: MarketData) -> None:
        """处理接收到的价格更新"""

        if not self.running or not self.strategy:
            return

        try:
            # 从交易所更新当前持仓
            self.current_positions = await self.exchange.get_positions()

            # 获取当前余额
            balance_info = await self.exchange.get_balance(
                "USD"
            )  # 假设为USD余额
            balance = balance_info.available

            # 风险管理检查
            if self.risk_manager:
                await self._handle_risk_events(market_data)

            # 从策略生成交易信号
            signals = self.strategy.generate_signals(
                market_data, self.current_positions, balance
            )

            # 执行信号
            for signal in signals:
                await self._execute_signal(signal)

        except Exception as e:
            self.logger.error(f"❌ Error handling price update: {e}")

    async def _handle_risk_events(self, market_data: MarketData) -> None:
        """处理风险管理事件"""

        try:
            # 获取账户指标
            account_metrics_data = await self.exchange.get_account_metrics()
            account_metrics = AccountMetrics(
                total_value=account_metrics_data.get("total_value", 0.0),
                total_pnl=account_metrics_data.get("total_pnl", 0.0),
                unrealized_pnl=account_metrics_data.get("unrealized_pnl", 0.0),
                realized_pnl=account_metrics_data.get("realized_pnl", 0.0),
                drawdown_pct=account_metrics_data.get("drawdown_pct", 0.0),
                positions_count=account_metrics_data.get("positions_count", 0),
                largest_position_pct=account_metrics_data.get(
                    "largest_position_pct", 0.0
                ),
            )

            # 评估风险事件
            market_data_dict = {market_data.asset: market_data}
            risk_events = self.risk_manager.evaluate_risks(
                self.current_positions, market_data_dict, account_metrics
            )

            # 处理风险事件
            for event in risk_events:
                await self._execute_risk_action(event)

        except Exception as e:
            self.logger.error(f"❌ Error handling risk events: {e}")

    async def _execute_risk_action(self, event: RiskEvent) -> None:
        """根据风险事件执行操作"""

        try:
            self.logger.warning(f"🚨 Risk Event: {event.reason}")

            if event.action == RiskAction.CLOSE_POSITION:
                success = await self.exchange.close_position(event.asset)
                if success:
                    self.logger.info(f"✅ Position closed for {event.asset}")
                else:
                    self.logger.error(f"❌ Failed to close position for {event.asset}")

            elif event.action == RiskAction.REDUCE_POSITION:
                # 目前关闭50%的持仓
                reduction_pct = 0.5
                current_positions = await self.exchange.get_positions()
                for pos in current_positions:
                    if pos.asset == event.asset:
                        reduce_size = abs(pos.size) * reduction_pct
                        success = await self.exchange.close_position(
                            event.asset, reduce_size
                        )
                        if success:
                            self.logger.info(
                                f"✅ Position reduced by {reduction_pct * 100}% for {event.asset}"
                            )
                        break

            elif event.action == RiskAction.CANCEL_ORDERS:
                cancelled = await self.exchange.cancel_all_orders()
                self.logger.info(f"✅ Cancelled {cancelled} orders")

            elif event.action == RiskAction.PAUSE_TRADING:
                self.logger.critical(f"⏸️ Trading paused due to: {event.reason}")
                if self.strategy:
                    self.strategy.is_active = False

            elif event.action == RiskAction.EMERGENCY_EXIT:
                self.logger.critical(f"🚨 EMERGENCY EXIT: {event.reason}")
                # 从交易所获取最新持仓并全部关闭
                current_positions = await self.exchange.get_positions()
                for pos in current_positions:
                    await self.exchange.close_position(pos.asset)
                # 取消所有订单
                await self.exchange.cancel_all_orders()
                # 停止交易
                if self.strategy:
                    self.strategy.is_active = False

        except Exception as e:
            self.logger.error(
                f"❌ Error executing risk action for {event.rule_name}: {e}"
            )

    async def _execute_signal(self, signal: TradingSignal) -> None:
        """执行交易信号"""

        try:
            if signal.signal_type in [SignalType.BUY, SignalType.SELL]:
                await self._place_order(signal)
            elif signal.signal_type == SignalType.CLOSE:
                await self._close_positions(signal)

        except Exception as e:
            self.logger.error(f"❌ Error executing signal: {e}")
            # 通知策略发生错误
            if self.strategy:
                self.strategy.on_error(e, {"signal": signal})

    async def _place_order(self, signal: TradingSignal) -> None:
        """根据交易信号下单"""

        # 创建订单
        current_time = time.time()
        order = Order(
            id=f"order_{int(current_time * 1000)}",  # 简单的ID生成
            asset=signal.asset,
            side=OrderSide.BUY
            if signal.signal_type == SignalType.BUY
            else OrderSide.SELL,
            size=signal.size,
            order_type=OrderType.LIMIT if signal.price else OrderType.MARKET,
            price=signal.price,
            created_at=current_time,
        )

        # 在交易所下单
        exchange_order_id = await self.exchange.place_order(order)
        order.exchange_order_id = exchange_order_id
        order.status = OrderStatus.SUBMITTED

        # 跟踪待处理订单
        self.pending_orders[order.id] = order

        self.logger.info(
            f"📝 Placed {order.side.value} order: {order.size} {order.asset} @ ${order.price}"
        )

        # 通知策略
        if self.strategy:
            # 目前模拟立即执行(实际实现会跟踪成交)
            executed_price = order.price or 0.0
            self.strategy.on_trade_executed(signal, executed_price, order.size)
            self.executed_trades += 1

    async def _close_positions(self, signal: TradingSignal) -> None:
        """关闭持仓(例如,为再平衡取消所有订单)"""

        if signal.metadata.get("action") == "cancel_all":
            cancelled = await self.exchange.cancel_all_orders()
            self.logger.info(f"🗑️ Cancelled {cancelled} orders for rebalancing")

    async def _trading_loop(self) -> None:
        """用于周期性任务的主交易循环"""

        while self.running:
            try:
                # 周期性健康检查、订单状态更新等
                await asyncio.sleep(60)  # 每分钟检查一次

                # 更新订单状态(简化版)
                await self._update_order_statuses()

                # 记录状态
                if self.executed_trades > 0:
                    self.logger.info(f"📊 Total trades: {self.executed_trades}")

            except Exception as e:
                self.logger.error(f"❌ Error in trading loop: {e}")
                await asyncio.sleep(60)

    async def _update_order_statuses(self) -> None:
        """更新待处理订单的状态"""

        # 这里会查询交易所获取订单状态
        # 目前仅清理旧订单
        current_time = time.time()

        for order_id in list(self.pending_orders.keys()):
            order = self.pending_orders[order_id]

            # 移除超过1小时的订单(可能已成交或已取消)
            if current_time - order.created_at > 3600:
                del self.pending_orders[order_id]

    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""

        return {
            "running": self.running,
            "strategy": self.strategy.get_status() if self.strategy else None,
            "exchange": self.exchange.get_status() if self.exchange else None,
            "market_data": self.market_data.get_status() if self.market_data else None,
            "risk_manager": self.risk_manager.get_status()
            if self.risk_manager
            else None,
            "executed_trades": self.executed_trades,
            "pending_orders": len(self.pending_orders),
            "current_positions": len(self.current_positions),
            "total_pnl": self.total_pnl,
        }
