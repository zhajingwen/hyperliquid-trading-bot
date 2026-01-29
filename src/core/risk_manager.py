"""
风险管理模块

处理所有风险相关决策,包括止损、止盈、回撤限制和仓位管理。
设计注重可扩展性和清晰度。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

from interfaces.strategy import Position, MarketData


class RiskAction(Enum):
    """违反风险规则时可采取的操作"""

    NONE = "none"
    CLOSE_POSITION = "close_position"
    REDUCE_POSITION = "reduce_position"
    CANCEL_ORDERS = "cancel_orders"
    PAUSE_TRADING = "pause_trading"
    EMERGENCY_EXIT = "emergency_exit"


@dataclass
class RiskEvent:
    """风险事件通知"""

    rule_name: str
    asset: str
    action: RiskAction
    reason: str
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    metadata: Dict[str, Any]
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class AccountMetrics:
    """用于风险评估的账户级别指标"""

    total_value: float
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    drawdown_pct: float
    positions_count: int
    largest_position_pct: float


class RiskRule(ABC):
    """
    风险规则的基础接口

    每个规则实现一个特定的风险检查(例如止损、回撤)
    并在发生违规时返回风险事件。
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def evaluate(
        self,
        positions: List[Position],
        market_data: Dict[str, MarketData],
        account_metrics: AccountMetrics,
    ) -> List[RiskEvent]:
        """
        评估风险规则,如果发生违规则返回事件

        参数:
            positions: 当前持仓
            market_data: 按资产分类的最新市场数据
            account_metrics: 账户级别指标

        返回:
            风险事件列表(如果没有违规则为空)
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """获取规则状态"""
        return {"name": self.name, "enabled": self.enabled, "config": self.config}


class StopLossRule(RiskRule):
    """止损风险规则 - 当损失超过阈值时关闭持仓"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("stop_loss", config)
        self.loss_pct = config.get("loss_pct", 5.0)

    def evaluate(
        self,
        positions: List[Position],
        market_data: Dict[str, MarketData],
        account_metrics: AccountMetrics,
    ) -> List[RiskEvent]:
        """检查止损条件"""

        if not self.enabled:
            return []

        events = []

        for position in positions:
            # 计算当前损失百分比
            if position.entry_price > 0:
                loss_pct = (
                    abs(
                        position.unrealized_pnl
                        / (position.entry_price * abs(position.size))
                    )
                    * 100
                )

                if loss_pct >= self.loss_pct:
                    events.append(
                        RiskEvent(
                            rule_name=self.name,
                            asset=position.asset,
                            action=RiskAction.CLOSE_POSITION,
                            reason=f"Stop loss triggered: {loss_pct:.2f}% loss exceeds {self.loss_pct}%",
                            severity="HIGH",
                            metadata={
                                "position_size": position.size,
                                "entry_price": position.entry_price,
                                "current_loss_pct": loss_pct,
                                "threshold_pct": self.loss_pct,
                                "unrealized_pnl": position.unrealized_pnl,
                            },
                        )
                    )

        return events


class TakeProfitRule(RiskRule):
    """止盈风险规则 - 当盈利超过阈值时关闭持仓"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("take_profit", config)
        self.profit_pct = config.get("profit_pct", 20.0)

    def evaluate(
        self,
        positions: List[Position],
        market_data: Dict[str, MarketData],
        account_metrics: AccountMetrics,
    ) -> List[RiskEvent]:
        """检查止盈条件"""

        if not self.enabled:
            return []

        events = []

        for position in positions:
            # 计算当前盈利百分比
            if position.entry_price > 0 and position.unrealized_pnl > 0:
                profit_pct = (
                    position.unrealized_pnl
                    / (position.entry_price * abs(position.size))
                ) * 100

                if profit_pct >= self.profit_pct:
                    events.append(
                        RiskEvent(
                            rule_name=self.name,
                            asset=position.asset,
                            action=RiskAction.CLOSE_POSITION,
                            reason=f"Take profit triggered: {profit_pct:.2f}% profit exceeds {self.profit_pct}%",
                            severity="MEDIUM",
                            metadata={
                                "position_size": position.size,
                                "entry_price": position.entry_price,
                                "current_profit_pct": profit_pct,
                                "threshold_pct": self.profit_pct,
                                "unrealized_pnl": position.unrealized_pnl,
                            },
                        )
                    )

        return events


class DrawdownRule(RiskRule):
    """回撤风险规则 - 当账户回撤超过阈值时停止交易"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("max_drawdown", config)
        self.max_drawdown_pct = config.get("max_drawdown_pct", 15.0)

    def evaluate(
        self,
        positions: List[Position],
        market_data: Dict[str, MarketData],
        account_metrics: AccountMetrics,
    ) -> List[RiskEvent]:
        """检查回撤条件"""

        if not self.enabled:
            return []

        events = []

        if account_metrics.drawdown_pct >= self.max_drawdown_pct:
            events.append(
                RiskEvent(
                    rule_name=self.name,
                    asset="ACCOUNT",
                    action=RiskAction.EMERGENCY_EXIT,
                    reason=f"Max drawdown exceeded: {account_metrics.drawdown_pct:.2f}% >= {self.max_drawdown_pct}%",
                    severity="CRITICAL",
                    metadata={
                        "current_drawdown_pct": account_metrics.drawdown_pct,
                        "max_drawdown_pct": self.max_drawdown_pct,
                        "total_pnl": account_metrics.total_pnl,
                        "account_value": account_metrics.total_value,
                    },
                )
            )

        return events


class PositionSizeRule(RiskRule):
    """仓位大小风险规则 - 防止单个持仓过大"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("max_position_size", config)
        self.max_position_size_pct = config.get("max_position_size_pct", 30.0)

    def evaluate(
        self,
        positions: List[Position],
        market_data: Dict[str, MarketData],
        account_metrics: AccountMetrics,
    ) -> List[RiskEvent]:
        """检查仓位大小条件"""

        if not self.enabled:
            return []

        events = []

        for position in positions:
            if account_metrics.total_value > 0:
                position_pct = (
                    position.current_value / account_metrics.total_value
                ) * 100

                if position_pct >= self.max_position_size_pct:
                    events.append(
                        RiskEvent(
                            rule_name=self.name,
                            asset=position.asset,
                            action=RiskAction.REDUCE_POSITION,
                            reason=f"Position too large: {position_pct:.2f}% >= {self.max_position_size_pct}%",
                            severity="MEDIUM",
                            metadata={
                                "position_value": position.current_value,
                                "account_value": account_metrics.total_value,
                                "position_pct": position_pct,
                                "max_position_pct": self.max_position_size_pct,
                                "suggested_reduction": position_pct
                                - self.max_position_size_pct,
                            },
                        )
                    )

        return events


class RiskManager:
    """
    主风险管理编排器

    协调多个风险规则并提供统一的风险评估。
    设计为可扩展 - 可以轻松添加新的风险规则。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules: List[RiskRule] = []
        self.risk_events_history: List[RiskEvent] = []

        # 根据配置初始化风险规则
        self._initialize_rules()

    def _initialize_rules(self):
        """从配置初始化风险规则"""

        risk_config = self.config.get("risk_management", {})

        # 止损规则
        if risk_config.get("stop_loss_enabled", False):
            self.rules.append(
                StopLossRule(
                    {"enabled": True, "loss_pct": risk_config.get("stop_loss_pct", 5.0)}
                )
            )

        # 止盈规则
        if risk_config.get("take_profit_enabled", False):
            self.rules.append(
                TakeProfitRule(
                    {
                        "enabled": True,
                        "profit_pct": risk_config.get("take_profit_pct", 20.0),
                    }
                )
            )

        # 回撤规则
        self.rules.append(
            DrawdownRule(
                {
                    "enabled": True,
                    "max_drawdown_pct": risk_config.get("max_drawdown_pct", 15.0),
                }
            )
        )

        # 仓位大小规则
        self.rules.append(
            PositionSizeRule(
                {
                    "enabled": True,
                    "max_position_size_pct": risk_config.get(
                        "max_position_size_pct", 30.0
                    ),
                }
            )
        )

    def evaluate_risks(
        self,
        positions: List[Position],
        market_data: Dict[str, MarketData],
        account_metrics: AccountMetrics,
    ) -> List[RiskEvent]:
        """
        评估所有风险规则并返回合并的风险事件

        参数:
            positions: 当前持仓
            market_data: 按资产分类的最新市场数据
            account_metrics: 账户级别指标

        返回:
            来自所有规则的风险事件列表
        """

        all_events = []

        for rule in self.rules:
            try:
                events = rule.evaluate(positions, market_data, account_metrics)
                all_events.extend(events)

                # 将事件存储到历史记录
                self.risk_events_history.extend(events)

            except Exception as e:
                # 记录错误但继续处理其他规则
                error_event = RiskEvent(
                    rule_name=rule.name,
                    asset="SYSTEM",
                    action=RiskAction.NONE,
                    reason=f"Risk rule evaluation failed: {e}",
                    severity="LOW",
                    metadata={"error": str(e)},
                )
                all_events.append(error_event)

        return all_events

    def add_rule(self, rule: RiskRule):
        """添加自定义风险规则"""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str):
        """按名称移除风险规则"""
        self.rules = [rule for rule in self.rules if rule.name != rule_name]

    def get_status(self) -> Dict[str, Any]:
        """获取风险管理器状态"""

        return {
            "enabled_rules": [rule.name for rule in self.rules if rule.enabled],
            "disabled_rules": [rule.name for rule in self.rules if not rule.enabled],
            "total_rules": len(self.rules),
            "recent_events": len(
                [
                    e
                    for e in self.risk_events_history
                    if time.time() - e.timestamp < 3600
                ]
            ),  # 最近一小时
            "config": self.config.get("risk_management", {}),
        }

    def get_recent_events(self, hours: int = 1) -> List[RiskEvent]:
        """获取最近的风险事件"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            event
            for event in self.risk_events_history
            if event.timestamp >= cutoff_time
        ]
