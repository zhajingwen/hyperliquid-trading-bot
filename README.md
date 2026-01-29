# Hyperliquid DEX 网格交易机器人

<div align="center">

**专业级自动化网格交易系统 for [Hyperliquid DEX](https://hyperliquid.xyz)**

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Hyperliquid](https://img.shields.io/badge/Hyperliquid-DEX-orange.svg)](https://hyperliquid.xyz)

</div>

> ⚠️ **风险提示**
>
> 本软件仅供教育和研究目的使用。交易加密货币涉及重大损失风险。切勿使用无法承受损失的资金进行交易。在实盘部署之前，请务必在测试网上充分测试策略。

---

## 📑 目录

- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [项目架构](#-项目架构)
- [配置系统](#️-配置系统)
- [网格交易策略](#-网格交易策略详解)
- [风险管理](#️-风险管理)
- [学习示例](#-学习示例)
- [API参考](#-api参考)
- [开发指南](#-开发指南)
- [故障排除](#-故障排除)
- [安全最佳实践](#-安全最佳实践)
- [路线图](#️-路线图)
- [贡献指南](#-贡献指南)

---

## ✨ 核心特性

### 🎯 交易功能
- **现货交易** - 直接资产持有（现金交易）
- **永续合约** - 杠杆衍生品交易
- **网格交易策略** - 跨价格区间的自动化买卖订单
- **实时市场数据** - WebSocket价格推送和订单簿数据

### 🛡️ 风险管理
- **止损/止盈** - 自动持仓退出
- **回撤限制** - 账户级别损失保护
- **仓位大小控制** - 防止过度暴露
- **网格再平衡** - 价格范围自适应

### 🏗️ 架构优势
- **SOLID原则** - 清晰的职责分离
- **接口驱动** - 易于扩展新交易所
- **事件驱动** - 高效的异步处理
- **配置化** - YAML配置，无需修改代码

### 📊 监控与分析
- **资金费率监控** - 永续合约成本跟踪
- **性能指标** - 实时盈亏和执行统计
- **结构化日志** - 完整的审计跟踪

---

## 🚀 快速开始

### 前置要求

1. **Python 3.13+** - 确保已安装最新版本Python
2. **[uv包管理器](https://github.com/astral-sh/uv)** - 快速、可靠的依赖管理
3. **Hyperliquid测试网账户** - 从[Chainstack水龙头](https://faucet.chainstack.com/hyperliquid-testnet-faucet)获取测试资金

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/chainstacklabs/hyperliquid-trading-bot
cd hyperliquid-trading-bot

# 2. 安装依赖
uv sync

# 3. 设置环境变量
cp .env.example .env
# 编辑.env文件，填入你的测试网私钥
```

### 环境配置

创建`.env`文件并配置：

```bash
# Hyperliquid测试网配置
HYPERLIQUID_TESTNET_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
HYPERLIQUID_TESTNET=true

# 可选：日志级别
LOG_LEVEL=INFO
```

💡 **提示**：你的私钥从不会被发送到任何服务器，仅用于本地签名交易。

### 快速运行

```bash
# 自动发现并运行第一个活动配置
uv run src/run_bot.py

# 运行前验证配置（推荐）
uv run src/run_bot.py --validate

# 运行特定配置文件
uv run src/run_bot.py bots/btc_conservative.yaml
```

---

## 🏗️ 项目架构

### 设计原则

本项目遵循**SOLID原则**，采用清晰的架构模式：

- **单一职责原则（SRP）** - 每个组件有明确的职责边界
- **开闭原则（OCP）** - 通过接口扩展，无需修改核心代码
- **里氏替换原则（LSP）** - 交易所适配器可互换
- **接口隔离原则（ISP）** - 最小化接口依赖
- **依赖倒置原则（DIP）** - 依赖抽象而非具体实现

### 核心组件

```
┌─────────────────────────────────────────────────────┐
│                   TradingEngine                      │
│            (核心编排层 - src/core/engine.py)          │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Strategy   │  │  Exchange    │  │    Risk    │  │
│  │  Interface  │  │  Adapter     │  │  Manager   │  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
│         ↑                ↑                  ↑         │
└─────────┼────────────────┼──────────────────┼─────────┘
          │                │                  │
    ┌─────┴─────┐    ┌────┴────┐      ┌─────┴──────┐
    │   Grid    │    │Hyperliq.│      │Stop Loss/  │
    │ Strategy  │    │ Adapter │      │Take Profit │
    └───────────┘    └─────────┘      └────────────┘
```

#### 1. **TradingEngine** (`src/core/engine.py`)
- 主编排器，协调所有组件
- 管理市场数据订阅
- 执行交易信号
- 处理订单生命周期

#### 2. **Strategy Interface** (`src/interfaces/strategy.py`)
- 定义交易策略的标准接口
- 策略通过实现接口来提供交易决策
- 支持多种策略类型（网格、均线、套利等）

#### 3. **Exchange Adapter** (`src/interfaces/exchange.py`)
- 统一的交易所抽象层
- 当前实现：Hyperliquid
- 易于添加新交易所（币安、OKX等）

#### 4. **Risk Manager** (`src/core/risk_manager.py`)
- 账户级别风险监控
- 止损/止盈执行
- 仓位大小控制
- 回撤保护

#### 5. **Market Data Provider** (`src/exchanges/hyperliquid/market_data.py`)
- WebSocket实时价格流
- 订单簿数据
- 交易历史

### 数据流

```
市场数据 (WebSocket)
    ↓
TradingEngine
    ↓
Strategy.on_market_data()
    ↓
生成 TradingSignal
    ↓
RiskManager.validate_signal()
    ↓
ExchangeAdapter.place_order()
    ↓
订单执行 & 状态更新
```

### 目录结构

```
hyperliquid-trading-bot/
├── src/
│   ├── run_bot.py                 # 主入口
│   ├── core/                      # 核心引擎
│   │   ├── engine.py              # 交易引擎
│   │   ├── enhanced_config.py     # 配置管理
│   │   ├── key_manager.py         # 私钥管理
│   │   ├── risk_manager.py        # 风险管理
│   │   └── endpoint_router.py     # API路由
│   ├── strategies/                # 交易策略
│   │   └── grid/
│   │       └── basic_grid.py      # 网格策略实现
│   ├── exchanges/                 # 交易所适配器
│   │   └── hyperliquid/
│   │       ├── adapter.py         # Hyperliquid集成
│   │       └── market_data.py     # 市场数据提供者
│   ├── interfaces/                # 业务接口
│   │   ├── strategy.py            # 策略接口
│   │   └── exchange.py            # 交易所接口
│   └── utils/                     # 工具类
│       ├── events.py              # 事件定义
│       └── exceptions.py          # 异常类
├── bots/                          # 机器人配置
│   └── btc_conservative.yaml      # 保守BTC策略
├── learning_examples/             # 教学脚本
│   ├── 01_websockets/             # WebSocket示例
│   ├── 02_market_data/            # 市场数据
│   ├── 03_account_info/           # 账户信息
│   ├── 04_trading/                # 交易操作
│   ├── 05_funding/                # 资金费率
│   └── 06_copy_trading/           # 复制交易
└── tests/                         # 测试套件
```

---

## ⚙️ 配置系统

### 配置文件结构

所有机器人配置存储在`bots/`目录的YAML文件中。每个配置文件定义一个完整的交易策略。

### 完整配置示例

```yaml
# bots/btc_conservative.yaml
name: "btc_conservative_clean"
active: true  # 设置为false可禁用此配置

# 交易所配置
exchange:
  type: "hyperliquid"  # 支持: hyperliquid, hl
  testnet: true        # true=测试网, false=主网

# 账户管理
account:
  max_allocation_pct: 10.0  # 使用账户余额的百分比 (1-100%)

# 网格策略参数
grid:
  symbol: "BTC"              # 交易对 (BTC, ETH, SOL等)
  levels: 10                 # 买卖订单数量 (3-50)

  price_range:
    mode: "auto"             # auto=自动计算, manual=手动设置
    auto:
      range_pct: 5.0         # 距中心价±%范围
    # manual:                # 手动模式示例
    #   upper_price: 45000.0
    #   lower_price: 35000.0

# 风险管理配置
risk_management:
  # 持仓退出策略
  stop_loss_enabled: false   # 启用止损
  stop_loss_pct: 8.0         # 止损百分比 (1-20%)

  take_profit_enabled: false # 启用止盈
  take_profit_pct: 25.0      # 止盈百分比 (5-100%)

  # 账户级别保护
  max_drawdown_pct: 15.0     # 最大回撤限制 (5-50%)
  max_position_size_pct: 40.0 # 单个仓位最大占比 (10-100%)

  # 网格再平衡
  rebalance:
    price_move_threshold_pct: 12.0  # 再平衡触发阈值

# 监控配置
monitoring:
  log_level: "INFO"          # DEBUG/INFO/WARNING/ERROR
```

### 配置参数详解

#### 账户配置 (`account`)

| 参数 | 范围 | 说明 | 推荐值 |
|------|------|------|--------|
| `max_allocation_pct` | 1-100% | 用于此策略的账户资金百分比 | 保守:5-10%, 激进:20-50% |

**💡 提示**：从小额分配开始（5-10%），验证策略有效后再增加。

#### 网格配置 (`grid`)

| 参数 | 范围 | 说明 | 推荐值 |
|------|------|------|--------|
| `symbol` | 字符串 | 交易对符号 | BTC, ETH, SOL |
| `levels` | 3-50 | 网格层级数量 | 保守:5-10, 激进:20-30 |
| `range_pct` | 1-50% | 价格范围宽度 | 震荡:3-8%, 趋势:10-20% |

**网格层级选择**：
- **5-10层** - 简单管理，适合初学者
- **10-20层** - 平衡频率和利润
- **20-30层** - 高频交易，适合窄幅震荡

**价格范围选择**：
- **3-5%** - 窄幅震荡市场
- **5-10%** - 正常波动市场
- **10-20%** - 高波动/趋势市场

#### 风险管理 (`risk_management`)

| 参数 | 范围 | 说明 | 推荐值 |
|------|------|------|--------|
| `stop_loss_pct` | 1-20% | 持仓损失触发平仓 | 5-10% |
| `take_profit_pct` | 5-100% | 持仓盈利触发平仓 | 15-30% |
| `max_drawdown_pct` | 5-50% | 账户回撤停止交易 | 10-20% |
| `max_position_size_pct` | 10-100% | 单个仓位最大占比 | 30-50% |
| `price_move_threshold_pct` | 5-50% | 再平衡触发阈值 | 10-15% |

**⚠️ 风险管理最佳实践**：
- 始终启用`max_drawdown_pct`保护账户
- 测试时使用严格的`stop_loss_pct`（3-5%）
- 避免`max_position_size_pct`超过50%

### 配置模板

#### 保守策略（低风险）
```yaml
account:
  max_allocation_pct: 10.0

grid:
  levels: 10
  price_range:
    mode: "auto"
    auto:
      range_pct: 5.0

risk_management:
  stop_loss_enabled: true
  stop_loss_pct: 5.0
  max_drawdown_pct: 10.0
  rebalance:
    price_move_threshold_pct: 12.0
```

#### 激进策略（高风险）
```yaml
account:
  max_allocation_pct: 30.0

grid:
  levels: 20
  price_range:
    mode: "auto"
    auto:
      range_pct: 15.0

risk_management:
  stop_loss_enabled: true
  stop_loss_pct: 10.0
  max_drawdown_pct: 20.0
  rebalance:
    price_move_threshold_pct: 8.0
```

---

## 📊 网格交易策略详解

### 什么是网格交易？

网格交易是一种量化交易策略，在预设价格区间内放置一系列买入和卖出限价单，形成"网格"。当价格波动时，自动执行低买高卖，从市场波动中获利。

### 网格交易原理

```
价格
  ↑
  │  卖单 ─────  $42,000 (Level 5)
  │  卖单 ─────  $41,000 (Level 4)
  │  卖单 ─────  $40,500 (Level 3)
  │
  │  中心价格 ──  $40,000
  │
  │  买单 ─────  $39,500 (Level 2)
  │  买单 ─────  $39,000 (Level 1)
  │  买单 ─────  $38,000 (Level 0)
  └──────────────────────────→
```

**工作流程**：
1. 在当前价格上下设置买卖订单
2. 价格下跌时，买单成交，持有资产
3. 价格上涨时，卖单成交，获取利润
4. 每次成交后重新放置订单

### 网格交易适用场景

✅ **适合的市场条件**：
- 横盘震荡市场（价格在区间内波动）
- 高波动性市场（频繁的价格波动）
- 缺乏明确趋势的市场

❌ **不适合的市场条件**：
- 强单边趋势市场（持续上涨或下跌）
- 极低波动市场（价格几乎不动）
- 流动性极差的市场

### 参数调优策略

#### 1. 网格层级数量 (`levels`)

**更多层级**：
- ✅ 交易机会更多
- ✅ 更平滑的成本平均
- ❌ 单笔利润更小
- ❌ 手续费占比更高

**更少层级**：
- ✅ 单笔利润更大
- ✅ 手续费占比更低
- ❌ 交易机会更少
- ❌ 成本平均效果差

**推荐配置**：
- **窄幅震荡（±3-5%）** → 15-25层
- **正常波动（±5-10%）** → 10-15层
- **宽幅波动（±10-20%）** → 5-10层

#### 2. 价格范围 (`range_pct`)

**窄范围（3-8%）**：
- ✅ 高成交频率
- ✅ 适合稳定币对
- ❌ 容易突破范围
- ❌ 频繁再平衡

**宽范围（10-20%）**：
- ✅ 覆盖更大波动
- ✅ 更少再平衡
- ❌ 成交频率低
- ❌ 资金效率低

**推荐配置**：
- **BTC/ETH** → 5-10%
- **主流币** → 8-15%
- **小市值币** → 15-25%

#### 3. 资金分配 (`max_allocation_pct`)

**风险等级**：
- **极保守** → 5-10%
- **保守** → 10-20%
- **中等** → 20-40%
- **激进** → 40-60%
- **极激进** → 60%+（不推荐）

### 不同市场条件的策略配置

#### 牛市配置（上涨趋势）
```yaml
grid:
  levels: 8
  price_range:
    mode: "auto"
    auto:
      range_pct: 8.0  # 更宽范围捕捉上涨

risk_management:
  stop_loss_pct: 8.0  # 较宽止损
  take_profit_pct: 20.0  # 较低止盈（让利润奔跑）
  rebalance:
    price_move_threshold_pct: 15.0  # 较高阈值避免频繁再平衡
```

#### 熊市配置（下跌趋势）
```yaml
grid:
  levels: 8
  price_range:
    mode: "auto"
    auto:
      range_pct: 8.0

risk_management:
  stop_loss_pct: 5.0  # 严格止损
  take_profit_pct: 10.0  # 快速获利
  rebalance:
    price_move_threshold_pct: 10.0
```

#### 震荡市配置（横盘）
```yaml
grid:
  levels: 15  # 更多层级
  price_range:
    mode: "auto"
    auto:
      range_pct: 5.0  # 窄范围高频

risk_management:
  stop_loss_pct: 8.0
  take_profit_pct: 15.0
  rebalance:
    price_move_threshold_pct: 12.0
```

### 风险收益权衡

| 配置 | 预期收益 | 风险等级 | 适合人群 |
|------|----------|----------|----------|
| 保守（5-10%分配，窄范围） | 低-中 | 低 | 初学者 |
| 平衡（10-20%分配，中范围） | 中 | 中 | 有经验者 |
| 激进（30%+分配，宽范围） | 中-高 | 高 | 专业交易者 |

---

## 🛡️ 风险管理

### 概述

风险管理系统提供多层保护机制，防止过度损失和控制风险暴露。

### 1. 持仓级别退出

#### 止损 (Stop Loss)

自动关闭亏损超过阈值的持仓。

```yaml
risk_management:
  stop_loss_enabled: true
  stop_loss_pct: 8.0  # 亏损8%时平仓
```

**工作原理**：
```
入场价格: $40,000
止损比例: 8%
触发价格: $36,800 (下跌8%)
→ 自动市价卖出全部持仓
```

**最佳实践**：
- 测试时使用3-5%（严格）
- 生产环境使用5-10%（合理）
- 避免超过15%（过宽）

#### 止盈 (Take Profit)

自动关闭盈利达到目标的持仓。

```yaml
risk_management:
  take_profit_enabled: true
  take_profit_pct: 25.0  # 盈利25%时平仓
```

**工作原理**：
```
入场价格: $40,000
止盈比例: 25%
触发价格: $50,000 (上涨25%)
→ 自动市价卖出全部持仓
```

**最佳实践**：
- 短期交易：10-20%
- 中期持有：20-40%
- 长期投资：50%+

### 2. 账户级别保护

#### 最大回撤限制 (Max Drawdown)

当账户整体损失超过阈值时停止所有交易。

```yaml
risk_management:
  max_drawdown_pct: 15.0  # 账户回撤15%时停止
```

**计算方式**：
```
初始账户: $10,000
当前余额: $8,600
回撤: ($10,000 - $8,600) / $10,000 = 14%
→ 接近15%限制，即将触发保护
```

**推荐设置**：
- 极保守：5-10%
- 保守：10-15%
- 中等：15-25%
- 激进：25-35%

#### 仓位大小限制 (Position Size)

限制单个仓位占账户资金的最大比例。

```yaml
risk_management:
  max_position_size_pct: 40.0  # 单仓位最多40%
```

**风险等级**：
- **10-20%** - 极保守
- **20-40%** - 保守
- **40-60%** - 激进
- **60%+** - 危险（不推荐）

### 3. 网格再平衡

当价格移出网格范围时，自动调整网格位置。

```yaml
risk_management:
  rebalance:
    price_move_threshold_pct: 12.0
```

**再平衡触发条件**：
```
网格范围: $38,000 - $42,000 (±5%)
中心价格: $40,000
阈值: 12%

当前价格: $44,800
价格变化: ($44,800 - $40,000) / $40,000 = 12%
→ 触发再平衡，重新计算网格
```

**再平衡流程**：
1. 取消所有未成交订单
2. 基于当前价格计算新网格
3. 放置新的买卖订单
4. 保留现有持仓（不强制平仓）

**阈值设置**：
- **5-8%** - 高频再平衡（高手续费）
- **8-12%** - 平衡（推荐）
- **12-20%** - 低频再平衡（可能错过机会）

### 4. 资金费率监控

⚠️ **重要**：资金费率是永续合约特有的成本，会显著影响盈利能力。

#### 什么是资金费率？

资金费率是永续合约的定期支付机制，确保合约价格锚定现货价格：

```
资金支付 = 仓位大小 × 预言机价格 × 资金费率
```

**支付频率**：Hyperliquid上每小时支付一次

**正负含义**：
- **正费率** → 多头支付给空头（多头过热）
- **负费率** → 空头支付给多头（空头过热）

#### 入场前检查清单

在开仓前评估资金费率影响：

##### ✅ 1. 费率方向检查
```yaml
# 决策规则
if 支付资金费率 AND 持仓时间 > 1小时:
    → 减小仓位或提高信号要求
```

**实例**：
```
计划开多仓 BTC
当前资金费率: +0.01% (多头支付)
持仓计划: 12小时
→ 你将支付12次资金费率
→ 考虑减少30-50%仓位
```

##### ✅ 2. 归一化到账户规模
```python
# 计算每日费率成本
日费率成本 = 名义价值 × 小时费率 × 24
费率消耗率 = 日费率成本 / 账户权益

# 风险阈值
if 费率消耗率 < 0.5%: 安全
elif 费率消耗率 < 1.0%: 谨慎
elif 费率消耗率 < 2.0%: 高风险
else: 禁止入场
```

**实例**：
```
账户权益: $10,000
仓位大小: $5,000 (5倍杠杆 × $1,000)
小时费率: +0.01%
日费率成本: $5,000 × 0.01% × 24 = $12
费率消耗率: $12 / $10,000 = 0.12% ✅ 安全
```

##### ✅ 3. 费率 vs 预期利润
```python
if 预期收益 < 2 × 日费率成本:
    → 交易不值得（手续费+资金费率会吃掉利润）
```

##### ✅ 4. 费率趋势分析
```python
# 检查费率加速
当前费率: 0.01%
3小时前: 0.005%
24小时前: 0.002%
→ 费率加速上升，多头过热
→ 避免做多或减小仓位
```

##### ✅ 5. 波动率调整杠杆上限
```python
# 高费率 + 高波动 = 降低杠杆
最大杠杆 = min(基础杠杆, 1 / 日费率%)

# 示例
日费率: 1% → 最大杠杆 = 1x
日费率: 0.5% → 最大杠杆 = 2x
日费率: 0.1% → 最大杠杆 = 10x
```

##### ✅ 6. 时间对齐
```python
# 持仓时间决定费率重要性
if 持仓时间 < 1小时: 费率无关紧要
elif 持仓时间 < 12小时: 费率需考虑
else: 费率至关重要
```

#### 持仓期间监控

##### ✅ 7. 实时费率消耗追踪
```python
# 维护指标
已支付费率 = 累计费率支付金额
费率消耗百分比 = 已支付费率 / 账户权益

# 硬止损
if 费率消耗 > 计划最大损失 × 30%:
    → 立即平仓（不要让费率慢慢吃掉账户）
```

##### ✅ 8. 监控清算距离缩小
```python
# 费率会减少权益，使清算价格向你靠近
ATR = 平均真实波幅
清算距离 = |入场价 - 清算价|
安全倍数 Y = 3-5

if 清算距离 < Y × ATR:
    → 减少仓位或平仓
```

**实例**：
```
做多 BTC
入场价: $40,000
清算价: $38,000
清算距离: $2,000

ATR (24h): $800
安全阈值: 3 × $800 = $2,400

$2,000 < $2,400 → ⚠️ 危险！
→ 减少仓位或平仓
```

##### ✅ 9. 费率反转警报
```python
# 费率改变符号时发出警告
if 费率[t] × 费率[t-1] < 0:
    → 拥挤方已改变
    → 收紧止损或部分平仓
```

#### 费率管理工具

1. **减少名义价值**（最佳）- 降低仓位大小
2. **降低杠杆** - 不改变费率但增加反应时间
3. **缩短持有期** - 减少费率支付次数
4. **反向偏差** - 费率不利时考虑反向
5. **临时对冲** - 使用现货对冲永续合约

#### 最小可行规则集

```yaml
# 入场规则
entry_rules:
  - funding_burn_pct < 1.0  # 日费率消耗 < 1%
  - funding_not_accelerating: true  # 费率未加速
  - expected_move > 2x_funding_cost  # 预期收益 > 2倍费率成本

# 持仓规则
position_rules:
  - exit_if_funding_loss > 30%_of_max_risk  # 费率损失超30%最大风险
  - exit_if_liquidation_distance < 3x_ATR  # 清算距离 < 3倍ATR
  - reduce_if_funding_spikes: true  # 费率连续飙升时减仓
```

#### 如何在机器人中实现

**查询资金费率**：
```bash
uv run learning_examples/05_funding/get_funding_rates.py
```

**检查现货/永续配对**（套利机会）：
```bash
uv run learning_examples/05_funding/check_spot_perp_pairs_availability.py
```

**实现费率监控**：
```python
from exchanges.hyperliquid.adapter import HyperliquidAdapter

adapter = HyperliquidAdapter()
meta = adapter.get_market_metadata()

for market in meta:
    if 'funding' in market:
        funding_rate = market['funding']
        print(f"{market['name']}: {funding_rate}%/hour")
```

📖 **详细指南**：查看 `learning_examples/05_funding/README.md` 获取完整的资金费率操作指南。

### 5. 优雅关闭

当机器人停止时的行为：

```python
# 默认行为
1. 取消所有待处理订单
2. 保留现有持仓（不强制平仓）
3. 记录最终状态
4. 清理资源
```

**⚠️ 注意**：机器人停止后，你的持仓仍然存在，请手动管理或重新启动机器人。

---

## 📚 学习示例

`learning_examples/`目录包含独立的教学脚本，帮助你掌握Hyperliquid API的各个方面。

### 📡 01. WebSocket 实时数据

#### 基础WebSocket连接
```bash
uv run learning_examples/01_websockets/realtime_prices.py
```
学习内容：
- 订阅单个交易对的实时价格
- 处理WebSocket消息
- 管理连接生命周期

#### 多订阅管理
```bash
uv run learning_examples/01_websockets/realtime_prices_multiple_subs.py
```
学习内容：
- 同时监控多个交易对
- 订阅管理最佳实践
- 消息路由和处理

#### 永续合约监控
```bash
# 使用原始WebSocket
uv run learning_examples/01_websockets/realtime_all_perpetuals.py

# 使用SDK封装
uv run learning_examples/01_websockets/realtime_all_perpetuals_sdk.py
```
学习内容：
- 订阅所有永续合约
- 批量数据处理
- 性能优化技巧

### 📊 02. 市场数据

#### 获取所有价格
```bash
uv run learning_examples/02_market_data/get_all_prices.py
```
学习内容：
- 查询所有交易对价格
- 价格数据结构解析
- 现货 vs 永续合约价格

#### 市场元数据
```bash
uv run learning_examples/02_market_data/get_market_metadata.py
```
学习内容：
- 获取交易规则（最小订单量、价格精度等）
- 市场状态查询
- 交易限制理解

### 👤 03. 账户信息

#### 用户状态查询
```bash
uv run learning_examples/03_account_info/get_user_state.py
```
学习内容：
- 查询账户余额
- 查看持仓信息
- 账户权益计算

#### 查看未成交订单
```bash
uv run learning_examples/03_account_info/get_open_orders.py
```
学习内容：
- 列出所有待处理订单
- 订单状态理解
- 订单过滤和排序

### 💹 04. 交易操作

#### 下限价单
```bash
uv run learning_examples/04_trading/place_limit_order.py
```
学习内容：
- 构造限价单
- 订单参数设置
- 订单确认处理

#### 取消订单
```bash
uv run learning_examples/04_trading/cancel_orders.py
```
学习内容：
- 单个订单取消
- 批量取消
- 取消全部订单

### 💰 05. 资金费率监控

#### 查询资金费率
```bash
uv run learning_examples/05_funding/get_funding_rates.py
```
学习内容：
- 获取当前资金费率
- 历史费率查询
- 费率趋势分析

#### 现货/永续配对检查
```bash
uv run learning_examples/05_funding/check_spot_perp_pairs_availability.py
```
学习内容：
- 查找同时支持现货和永续的资产
- 识别套利机会
- 现货-永续价差分析

#### 资金费率详细指南
📖 **完整教程**：`learning_examples/05_funding/README.md`

涵盖内容：
- 资金费率工作原理
- 入场前风险评估
- 持仓期间监控策略
- 实战决策规则

### 🔄 06. 复制交易

#### 镜像现货订单
```bash
uv run learning_examples/06_copy_trading/mirror_spot_orders.py
```
学习内容：
- 监听目标账户订单
- 自动复制订单
- 仓位比例控制

#### TWAP订单复制
```bash
uv run learning_examples/06_copy_trading/mirror_spot_twap_orders.py
```
学习内容：
- 时间加权平均价格（TWAP）策略
- 大额订单分批执行
- 减少价格冲击

#### 原始WebSocket消息
```bash
uv run learning_examples/06_copy_trading/print_raw_websocket_messages.py
```
学习内容：
- WebSocket消息结构
- 调试技巧
- 自定义事件处理

#### 解析用户事件
```bash
uv run learning_examples/06_copy_trading/print_parsed_user_events.py
```
学习内容：
- 用户事件类型
- 事件解析逻辑
- 构建自定义监控

### 📖 学习路径建议

#### 初学者路径
1. **市场数据** → 理解数据结构
2. **WebSocket** → 实时数据订阅
3. **账户信息** → 查询账户状态
4. **交易操作** → 下单和取消

#### 中级路径
5. **资金费率** → 理解永续合约成本
6. **复制交易基础** → 订单镜像

#### 高级路径
7. **TWAP策略** → 高级订单执行
8. **WebSocket调试** → 自定义事件处理

---

## 🔌 API参考

### 核心接口

#### TradingStrategy (`src/interfaces/strategy.py`)

定义所有交易策略必须实现的接口。

```python
from interfaces.strategy import TradingStrategy, TradingSignal, MarketData

class MyStrategy(TradingStrategy):
    async def on_start(self) -> None:
        """策略启动时调用"""
        pass

    async def on_market_data(self, data: MarketData) -> List[TradingSignal]:
        """处理市场数据，返回交易信号"""
        signals = []
        # 你的策略逻辑
        return signals

    async def on_order_update(self, order: Order) -> None:
        """订单状态更新时调用"""
        pass

    async def on_stop(self) -> None:
        """策略停止时调用"""
        pass
```

**MarketData结构**：
```python
@dataclass
class MarketData:
    symbol: str           # 交易对
    timestamp: float      # Unix时间戳
    price: float          # 当前价格
    volume_24h: float     # 24小时交易量
    bid: Optional[float]  # 最佳买价
    ask: Optional[float]  # 最佳卖价
```

**TradingSignal结构**：
```python
@dataclass
class TradingSignal:
    signal_type: SignalType  # BUY, SELL, CLOSE
    symbol: str              # 交易对
    size: float              # 订单大小
    price: Optional[float]   # 限价（None=市价）
    reason: str              # 信号原因（用于日志）
```

#### ExchangeAdapter (`src/interfaces/exchange.py`)

交易所适配器接口，所有交易所实现必须遵循。

```python
from interfaces.exchange import ExchangeAdapter, Order, OrderSide, OrderType

class MyExchangeAdapter(ExchangeAdapter):
    async def connect(self) -> None:
        """建立交易所连接"""
        pass

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,      # BUY / SELL
        order_type: OrderType,  # LIMIT / MARKET
        size: float,
        price: Optional[float] = None
    ) -> Order:
        """下单"""
        pass

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        pass

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取未成交订单"""
        pass

    async def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        pass

    async def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        pass
```

**Order结构**：
```python
@dataclass
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    size: float
    price: Optional[float]
    status: OrderStatus  # PENDING, FILLED, CANCELLED, REJECTED
    filled_size: float
    timestamp: float
```

### Hyperliquid适配器

#### HyperliquidAdapter (`src/exchanges/hyperliquid/adapter.py`)

Hyperliquid交易所的具体实现。

```python
from exchanges.hyperliquid import HyperliquidAdapter

# 初始化
adapter = HyperliquidAdapter(
    testnet=True,  # True=测试网, False=主网
    private_key="0x..."
)

# 连接
await adapter.connect()

# 下限价单
order = await adapter.place_order(
    symbol="BTC",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    size=0.01,  # 0.01 BTC
    price=40000.0
)

# 下市价单
order = await adapter.place_order(
    symbol="BTC",
    side=OrderSide.SELL,
    order_type=OrderType.MARKET,
    size=0.01
)

# 取消订单
success = await adapter.cancel_order(order.order_id)

# 查询余额
balance = await adapter.get_account_balance()
print(f"USDC余额: {balance['USDC']}")

# 查询持仓
position = await adapter.get_position("BTC")
if position:
    print(f"持仓大小: {position.size}")
```

#### HyperliquidMarketData (`src/exchanges/hyperliquid/market_data.py`)

实时市场数据提供者。

```python
from exchanges.hyperliquid import HyperliquidMarketData

# 初始化
market_data = HyperliquidMarketData(testnet=True)

# 启动WebSocket连接
await market_data.start()

# 订阅价格更新
async def on_price_update(data: MarketData):
    print(f"{data.symbol}: ${data.price}")

market_data.subscribe("BTC", on_price_update)

# 取消订阅
market_data.unsubscribe("BTC")

# 停止
await market_data.stop()
```

### 风险管理器

#### RiskManager (`src/core/risk_manager.py`)

风险管理和账户保护。

```python
from core.risk_manager import RiskManager, RiskEvent, RiskAction

# 初始化
risk_manager = RiskManager(config)

# 更新账户指标
risk_manager.update_account_metrics(
    equity=10000.0,
    position_value=3000.0,
    unrealized_pnl=-200.0
)

# 检查交易信号
risk_events = risk_manager.check_signal(signal)

for event in risk_events:
    if event.action == RiskAction.REJECT_SIGNAL:
        print(f"信号被拒绝: {event.reason}")
    elif event.action == RiskAction.CLOSE_POSITION:
        print(f"触发平仓: {event.reason}")
    elif event.action == RiskAction.STOP_TRADING:
        print(f"停止交易: {event.reason}")

# 检查持仓
risk_events = risk_manager.check_position(position, current_price)
```

---

## 🛠️ 开发指南

### 代码风格

本项目遵循Python最佳实践：

- **格式化**: 使用`black`格式化代码
- **导入排序**: 使用`isort`管理导入
- **类型检查**: 使用`mypy`进行静态类型检查
- **文档字符串**: 所有公共接口必须有文档字符串

```bash
# 格式化代码
black src/

# 排序导入
isort src/

# 类型检查
mypy src/
```

### 添加新交易策略

#### 1. 创建策略文件

在`src/strategies/`下创建新策略：

```python
# src/strategies/my_strategy/my_strategy.py
from typing import List
from interfaces.strategy import TradingStrategy, TradingSignal, MarketData, SignalType

class MyStrategy(TradingStrategy):
    """
    我的自定义策略

    策略描述：...
    """

    def __init__(self, config: dict):
        self.config = config
        # 初始化策略状态

    async def on_start(self) -> None:
        """策略启动"""
        print("策略启动")

    async def on_market_data(self, data: MarketData) -> List[TradingSignal]:
        """
        处理市场数据

        Args:
            data: 市场数据

        Returns:
            交易信号列表
        """
        signals = []

        # 你的策略逻辑
        if self.should_buy(data):
            signals.append(TradingSignal(
                signal_type=SignalType.BUY,
                symbol=data.symbol,
                size=self.calculate_size(),
                price=data.price * 0.99,  # 限价低1%
                reason="买入信号触发"
            ))

        return signals

    def should_buy(self, data: MarketData) -> bool:
        """判断是否应该买入"""
        # 你的买入逻辑
        return False

    def calculate_size(self) -> float:
        """计算订单大小"""
        # 你的仓位计算逻辑
        return 0.01
```

#### 2. 注册策略

在`src/core/engine.py`中注册策略：

```python
from strategies.my_strategy import MyStrategy

# 策略映射
STRATEGIES = {
    "grid": BasicGridStrategy,
    "my_strategy": MyStrategy,  # 添加你的策略
}
```

#### 3. 创建配置文件

在`bots/`目录创建配置：

```yaml
# bots/my_strategy_config.yaml
name: "my_strategy_btc"
active: true

exchange:
  type: "hyperliquid"
  testnet: true

strategy:
  type: "my_strategy"  # 策略类型
  # 你的策略参数
  param1: value1
  param2: value2

account:
  max_allocation_pct: 10.0

risk_management:
  stop_loss_enabled: true
  stop_loss_pct: 5.0
```

#### 4. 测试策略

```bash
# 验证配置
uv run src/run_bot.py --validate bots/my_strategy_config.yaml

# 运行策略
uv run src/run_bot.py bots/my_strategy_config.yaml
```

### 添加新交易所

#### 1. 创建适配器

实现`ExchangeAdapter`接口：

```python
# src/exchanges/new_exchange/adapter.py
from interfaces.exchange import ExchangeAdapter, Order, OrderSide, OrderType
from typing import List, Optional, Dict

class NewExchangeAdapter(ExchangeAdapter):
    """新交易所适配器"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.client = None

    async def connect(self) -> None:
        """建立连接"""
        # 初始化交易所客户端
        pass

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        size: float,
        price: Optional[float] = None
    ) -> Order:
        """下单"""
        # 调用交易所API
        pass

    # 实现其他接口方法...
```

#### 2. 创建市场数据提供者

```python
# src/exchanges/new_exchange/market_data.py
from typing import Callable, Dict
from interfaces.strategy import MarketData

class NewExchangeMarketData:
    """新交易所市场数据"""

    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.subscriptions: Dict[str, Callable] = {}

    async def start(self) -> None:
        """启动WebSocket连接"""
        pass

    def subscribe(self, symbol: str, callback: Callable) -> None:
        """订阅价格更新"""
        self.subscriptions[symbol] = callback

    async def stop(self) -> None:
        """停止连接"""
        pass
```

#### 3. 注册交易所

在`src/core/engine.py`中注册：

```python
from exchanges.new_exchange import NewExchangeAdapter

EXCHANGES = {
    "hyperliquid": HyperliquidAdapter,
    "new_exchange": NewExchangeAdapter,  # 添加新交易所
}
```

#### 4. 更新配置模式

在`src/core/enhanced_config.py`中添加验证：

```python
SUPPORTED_EXCHANGES = ["hyperliquid", "hl", "new_exchange"]
```

### 测试要求

#### 单元测试

```python
# tests/test_my_strategy.py
import pytest
from strategies.my_strategy import MyStrategy

@pytest.mark.asyncio
async def test_strategy_initialization():
    """测试策略初始化"""
    config = {"param1": "value1"}
    strategy = MyStrategy(config)
    assert strategy.config == config

@pytest.mark.asyncio
async def test_buy_signal():
    """测试买入信号"""
    strategy = MyStrategy({})
    data = MarketData(
        symbol="BTC",
        timestamp=time.time(),
        price=40000.0,
        volume_24h=1000000.0
    )

    signals = await strategy.on_market_data(data)
    assert len(signals) > 0
    assert signals[0].signal_type == SignalType.BUY
```

运行测试：
```bash
uv run pytest tests/
```

#### 集成测试

在测试网上测试完整流程：

```bash
# 1. 验证配置
uv run src/run_bot.py --validate bots/test_config.yaml

# 2. 短时间运行
# 手动停止后检查日志和订单

# 3. 验证行为
# - 订单是否正确下达？
# - 风险管理是否生效？
# - 日志是否完整？
```

---

## 🔍 故障排除

### 常见问题

#### 1. WebSocket连接失败

**症状**：
```
Error: WebSocket connection failed
```

**解决方案**：
```bash
# 检查网络连接
ping api.hyperliquid-testnet.xyz

# 检查防火墙设置
# 确保允许WebSocket连接（端口443）

# 尝试使用代理
export HTTPS_PROXY=http://proxy:port
```

#### 2. 订单被拒绝

**症状**：
```
Order rejected: insufficient balance
```

**解决方案**：
```python
# 检查账户余额
uv run learning_examples/03_account_info/get_user_state.py

# 减小订单大小
# 在配置中调整 max_allocation_pct

# 检查最小订单量
uv run learning_examples/02_market_data/get_market_metadata.py
```

#### 3. 精度错误

**症状**：
```
Order rejected: invalid price precision
```

**解决方案**：
```python
# BTC需要5位小数
price = round(40123.456789, 5)  # → 40123.45679

# 查看交易对精度要求
metadata = adapter.get_market_metadata()
print(metadata['BTC']['szDecimals'])  # 大小精度
print(metadata['BTC']['priceDecimals'])  # 价格精度
```

#### 4. 私钥错误

**症状**：
```
Error: Invalid private key format
```

**解决方案**：
```bash
# 确保私钥格式正确
# 正确: 0x1234567890abcdef...
# 错误: 1234567890abcdef...

# 检查.env文件
cat .env | grep PRIVATE_KEY

# 确保没有引号
# 错误: HYPERLIQUID_TESTNET_PRIVATE_KEY="0x..."
# 正确: HYPERLIQUID_TESTNET_PRIVATE_KEY=0x...
```

### 调试技巧

#### 启用详细日志

```yaml
# 在配置文件中设置
monitoring:
  log_level: "DEBUG"
```

或通过环境变量：
```bash
LOG_LEVEL=DEBUG uv run src/run_bot.py
```

#### 检查订单状态

```python
# 查看所有未成交订单
uv run learning_examples/03_account_info/get_open_orders.py

# 查看账户状态
uv run learning_examples/03_account_info/get_user_state.py
```

#### 监控WebSocket消息

```bash
# 查看原始WebSocket消息
uv run learning_examples/06_copy_trading/print_raw_websocket_messages.py
```

#### 验证配置

```bash
# 运行前验证
uv run src/run_bot.py --validate bots/your_config.yaml
```

### 性能优化

#### 1. 减少API调用

```python
# 不好：每次都查询
for symbol in symbols:
    price = await adapter.get_price(symbol)  # N次API调用

# 好：批量查询
prices = await adapter.get_all_prices()  # 1次API调用
```

#### 2. 使用WebSocket而非轮询

```python
# 不好：轮询价格
while True:
    price = await adapter.get_price("BTC")
    await asyncio.sleep(1)

# 好：WebSocket推送
market_data.subscribe("BTC", on_price_update)
```

#### 3. 优化网格层级

```yaml
# 层级过多会增加订单管理开销
grid:
  levels: 15  # 合理
  # levels: 50  # 避免（性能差）
```

#### 4. 合理设置再平衡阈值

```yaml
# 过低的阈值会导致频繁再平衡
rebalance:
  price_move_threshold_pct: 10.0  # 合理
  # price_move_threshold_pct: 3.0  # 避免（频繁）
```

---

## 🔒 安全最佳实践

### 私钥管理

#### ✅ 正确做法

1. **使用环境变量**
```bash
# .env文件（不提交到git）
HYPERLIQUID_TESTNET_PRIVATE_KEY=0x...
```

2. **使用专用测试账户**
```
- 测试网使用专用私钥
- 主网使用独立账户（不要用主账户）
- 限制账户资金（只存放交易所需金额）
```

3. **轮换私钥**
```
- 定期更换私钥
- 泄露后立即轮换
- 使用硬件钱包生成
```

#### ❌ 错误做法

```python
# 不要硬编码私钥
PRIVATE_KEY = "0x1234..."  # 危险！

# 不要提交.env到git
git add .env  # 危险！

# 不要在日志中打印私钥
logger.info(f"Key: {private_key}")  # 危险！
```

### API密钥安全

```bash
# 使用只读API密钥进行查询
# 交易使用权限最小的API密钥

# 限制API密钥IP白名单
# 在交易所设置中添加服务器IP
```

### 资金安全

#### 1. 分阶段部署

```
阶段1: 测试网 → 验证策略逻辑
阶段2: 主网小额 → 验证真实环境
阶段3: 逐步增加 → 扩大资金规模
```

#### 2. 设置硬限制

```yaml
# 限制最大分配
account:
  max_allocation_pct: 10.0  # 最多10%

# 启用回撤保护
risk_management:
  max_drawdown_pct: 15.0
```

#### 3. 监控和告警

```python
# 实现账户监控
if current_balance < initial_balance * 0.9:
    send_alert("账户余额下降10%")

if unrealized_pnl < -max_loss:
    send_alert("触发最大损失")
    stop_trading()
```

### 日志安全

#### 安全的日志实践

```python
# 不要记录敏感信息
logger.info(f"Order placed: {order.order_id}")  # ✅

# 不要记录私钥或密钥
logger.info(f"Using key: {private_key}")  # ❌

# 过滤敏感字段
safe_config = {k: v for k, v in config.items()
               if k not in ['private_key', 'api_secret']}
logger.info(f"Config: {safe_config}")  # ✅
```

### 网络安全

```bash
# 使用HTTPS和WSS
# Hyperliquid默认使用加密连接

# 考虑使用VPN
# 特别是在公共网络上运行时

# 启用防火墙
# 只允许必要的出站连接
```

---

## 🗺️ 路线图

### 已完成 ✅

- [x] 基础网格交易策略
- [x] Hyperliquid DEX集成
- [x] 现货交易支持
- [x] 永续合约支持
- [x] WebSocket实时数据
- [x] 风险管理系统
- [x] 配置化架构
- [x] 学习示例套件
- [x] 资金费率监控

### 开发中 🚧

- [ ] 回测系统
- [ ] 性能分析工具
- [ ] Web监控界面
- [ ] 多策略并行

### 计划中 📋

#### 策略增强
- [ ] 动态网格（自适应层级和范围）
- [ ] 马丁格尔策略
- [ ] DCA（定投）策略
- [ ] 套利策略（现货-永续）
- [ ] 趋势跟踪策略

#### 交易所集成
- [ ] 币安集成
- [ ] OKX集成
- [ ] Bybit集成

#### 功能增强
- [ ] 订单簿深度分析
- [ ] 滑点优化
- [ ] 智能订单路由
- [ ] 复制交易功能
- [ ] Telegram通知

#### 分析工具
- [ ] 策略回测引擎
- [ ] 性能报告生成
- [ ] 风险分析仪表板
- [ ] 交易日志分析

#### 基础设施
- [ ] Docker容器化
- [ ] 云部署指南
- [ ] 监控和告警系统
- [ ] 数据库集成（持久化）

---

## 🤝 贡献指南

欢迎贡献！本项目正在积极开发中。

### 如何贡献

#### 1. 报告问题

在GitHub Issues中报告：
- Bug报告
- 功能请求
- 文档改进建议

#### 2. 提交代码

```bash
# 1. Fork仓库
# 2. 创建功能分支
git checkout -b feature/my-feature

# 3. 提交更改
git commit -m "feat: add my feature"

# 4. 推送到分支
git push origin feature/my-feature

# 5. 创建Pull Request
```

#### 3. 代码审查清单

提交前确保：
- [ ] 代码通过所有测试
- [ ] 添加了新测试（如果适用）
- [ ] 更新了文档
- [ ] 遵循代码风格指南
- [ ] 通过类型检查（mypy）
- [ ] 格式化代码（black, isort）

### 提交消息规范

使用[Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: 添加新功能
fix: 修复bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构（不修复bug或添加功能）
test: 添加测试
chore: 构建过程或辅助工具变动
```

示例：
```bash
git commit -m "feat(strategies): add martingale strategy"
git commit -m "fix(risk): correct drawdown calculation"
git commit -m "docs(readme): update installation steps"
```

### 开发环境设置

```bash
# 安装开发依赖
uv sync --all-extras

# 运行测试
uv run pytest

# 代码格式化
uv run black src/
uv run isort src/

# 类型检查
uv run mypy src/
```

---

## 📄 许可证

本项目采用 **MIT许可证**。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

### 技术栈
- [Hyperliquid](https://hyperliquid.xyz) - 高性能去中心化交易所
- [uv](https://github.com/astral-sh/uv) - 快速Python包管理器
- [hyperliquid-python-sdk](https://github.com/hyperliquid-dex/python-sdk) - 官方Python SDK

### 文档和资源
- [Chainstack Developer Portal](https://docs.chainstack.com/docs/developer-portal-mcp-server) - Hyperliquid API文档
- [Chainstack Hyperliquid Faucet](https://faucet.chainstack.com/hyperliquid-testnet-faucet) - 测试网水龙头

### 社区
感谢所有贡献者和社区成员的支持！

---

## 📞 支持和社区

### 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/chainstacklabs/hyperliquid-trading-bot/issues)
- **讨论**: [GitHub Discussions](https://github.com/chainstacklabs/hyperliquid-trading-bot/discussions)

### 保持联系

- 关注项目获取更新
- ⭐ Star本仓库以示支持
- 🔔 Watch接收通知

---

<div align="center">

**免责声明**

本软件按"原样"提供，不提供任何明示或暗示的保证。作者不对使用本软件造成的任何损失负责。加密货币交易涉及重大风险，请谨慎操作。

---

**用❤️构建** | [GitHub](https://github.com/chainstacklabs/hyperliquid-trading-bot) | [Chainstack](https://chainstack.com)

</div>
