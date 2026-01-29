## [Hyperliquid DEX](https://hyperliquid.xyz)的可扩展网格交易机器人

> ⚠️ 本软件仅供教育和研究目的使用。交易加密货币涉及重大损失风险。切勿使用无法承受损失的资金进行交易。在实盘部署之前，请务必在测试网上充分测试策略。

本项目正在积极开发中。欢迎通过GitHub提交问题、建议和议题。

欢迎通过[Chainstack开发者门户MCP服务器](https://docs.chainstack.com/docs/developer-portal-mcp-server)使用Hyperliquid API的最佳文档。

## 🚀 快速开始

### **前置要求**
- [uv包管理器](https://github.com/astral-sh/uv)
- Hyperliquid测试网账户及测试网资金（参见[Chainstack Hyperliquid水龙头](https://faucet.chainstack.com/hyperliquid-testnet-faucet)）

### **安装**

```bash
# 克隆仓库
git clone https://github.com/chainstacklabs/hyperliquid-trading-bot
cd hyperliquid-trading-bot

# 使用uv安装依赖
uv sync

# 设置环境变量
cp .env.example .env
# 编辑.env文件，填入你的Hyperliquid测试网私钥
```

### **配置**

创建你的环境文件：
```bash
# .env
HYPERLIQUID_TESTNET_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
HYPERLIQUID_TESTNET=true
```

机器人附带了一个预配置的保守BTC网格策略，位于`bots/btc_conservative.yaml`。请根据需要查看和调整参数。

### **运行机器人**

```bash
# 自动发现并运行第一个活动配置
uv run src/run_bot.py

# 运行前验证配置
uv run src/run_bot.py --validate

# 运行特定配置
uv run src/run_bot.py bots/btc_conservative.yaml
```

## ⚙️ 配置

机器人配置使用YAML格式，包含全面的参数文档：

```yaml
# 保守BTC网格策略
name: "btc_conservative_clean"
active: true  # 启用/禁用此策略

account:
  max_allocation_pct: 10.0  # 仅使用账户余额的10%

grid:
  symbol: "BTC"
  levels: 10               # 网格层级数量
  price_range:
    mode: "auto"           # 根据当前价格自动计算
    auto:
      range_pct: 5.0      # ±5%价格范围（保守）

risk_management:
  # 退出策略
  stop_loss_enabled: false      # 在损失阈值时自动平仓
  stop_loss_pct: 8.0           # 平仓前的损失百分比（1-20%）
  take_profit_enabled: false   # 在利润阈值时自动平仓
  take_profit_pct: 25.0        # 平仓前的利润百分比（5-100%）

  # 账户保护
  max_drawdown_pct: 15.0       # 在账户回撤百分比时停止交易（5-50%）
  max_position_size_pct: 40.0  # 仓位占账户的最大百分比（10-100%）

  # 网格再平衡
  rebalance:
    price_move_threshold_pct: 12.0  # 再平衡触发器

monitoring:
  log_level: "INFO"       # DEBUG/INFO/WARNING/ERROR
```

## 📚 学习示例

通过独立的教学脚本掌握Hyperliquid API：

```bash
# 身份验证和连接
uv run learning_examples/01_authentication/basic_connection.py

# 市场数据和价格
uv run learning_examples/02_market_data/get_all_prices.py
uv run learning_examples/02_market_data/get_market_metadata.py

# 账户信息
uv run learning_examples/03_account_info/get_user_state.py
uv run learning_examples/03_account_info/get_open_orders.py

# 交易操作
uv run learning_examples/04_trading/place_limit_order.py
uv run learning_examples/04_trading/cancel_orders.py

# 实时数据
uv run learning_examples/05_websockets/realtime_prices.py
```

## 🛡️ 退出策略

机器人包含自动风险管理和持仓退出功能：

**持仓级别退出：**
- **止损**：当损失超过配置的百分比时自动平仓（1-20%）
- **止盈**：当利润超过配置的百分比时自动平仓（5-100%）

**账户级别保护：**
- **最大回撤**：当账户级别损失超过阈值时停止所有交易（5-50%）
- **仓位大小限制**：防止单个仓位超过账户的百分比（10-100%）

**操作退出：**
- **网格再平衡**：当价格移出范围时取消订单并重新创建网格
- **优雅关闭**：机器人终止时取消待处理订单（默认保留持仓）

所有退出策略都可按机器人配置，默认为禁用以确保安全。

## 🔧 开发

### **包管理**
本项目使用[uv](https://github.com/astral-sh/uv)进行快速、可靠的依赖管理：

```bash
uv sync              # 安装/同步依赖
uv add <package>     # 添加新依赖
uv run <command>     # 在虚拟环境中运行命令
```

### **测试**
所有组件均在Hyperliquid测试网上进行测试：

```bash
# 测试学习示例
uv run learning_examples/04_trading/place_limit_order.py

# 验证机器人配置
uv run src/run_bot.py --validate

# 在测试网模式下运行机器人（默认）
uv run src/run_bot.py
```
