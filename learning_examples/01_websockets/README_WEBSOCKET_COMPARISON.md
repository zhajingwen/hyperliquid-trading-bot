# WebSocket 实现方式对比

本目录提供了两种监控所有永续合约价格的实现方式：

## 1. 原始 WebSocket 实现

**文件**: `realtime_all_perpetuals.py`

**特点**:
- 使用 `websockets` 库直接连接 WebSocket
- 完全控制连接、订阅和消息处理流程
- 需要手动管理连接状态和重连逻辑
- 更灵活，适合学习 WebSocket 协议

**核心代码**:
```python
import websockets

async with websockets.connect(WS_URL) as websocket:
    # 发送订阅消息
    subscribe_msg = {"method": "subscribe", "subscription": {"type": "allMids"}}
    await websocket.send(json.dumps(subscribe_msg))

    # 接收消息
    async for message in websocket:
        data = json.loads(message)
        if data.get("channel") == "allMids":
            await self.handle_price_update(data)
```

**优点**:
- ✅ 完全控制 WebSocket 连接
- ✅ 清晰展示 WebSocket 协议细节
- ✅ 易于调试和理解底层机制

**缺点**:
- ❌ 需要手动处理重连、错误恢复
- ❌ 代码量更多
- ❌ 需要自行管理订阅状态

## 2. SDK WebSocket 实现

**文件**: `realtime_all_perpetuals_sdk.py`

**特点**:
- 使用官方 `hyperliquid-python-sdk` 的内置 WebSocket 功能
- SDK 自动管理连接、重连和订阅
- 代码更简洁，更易维护
- 适合生产环境使用

**核心代码**:
```python
from hyperliquid.info import Info

# 初始化 Info 类（skip_ws=False 启用 WebSocket）
self.info = Info(base_url, skip_ws=False)

# 订阅所有资产价格
subscription = {"type": "allMids"}
subscription_id = self.info.subscribe(subscription, self.handle_price_update)
```

**优点**:
- ✅ 代码简洁，易于维护
- ✅ SDK 自动处理重连和错误恢复
- ✅ 官方支持，与 SDK 其他功能无缝集成
- ✅ 生产环境推荐使用

**缺点**:
- ❌ 对底层 WebSocket 细节的控制较少
- ❌ 依赖 SDK 版本更新

## 订阅格式说明

### 支持的订阅类型

SDK 支持多种订阅类型，需要提供正确的字典格式：

```python
# 所有资产中价
{"type": "allMids"}

# 特定资产订单簿
{"type": "l2Book", "coin": "BTC"}

# 特定资产交易记录
{"type": "trades", "coin": "ETH"}

# K线数据
{"type": "candle", "coin": "SOL", "interval": "1m"}

# 最佳买卖价
{"type": "bbo", "coin": "BTC"}

# 用户账户事件
{"type": "user", "user": "0x..."}

# 用户成交记录
{"type": "userFills", "user": "0x..."}

# 资金费率
{"type": "activeAssetCtx", "coin": "BTC"}

# 清算事件
{"type": "liquidations", "coin": "BTC"}
```

## 运行示例

```bash
# 原始 WebSocket 版本
uv run learning_examples/01_websockets/realtime_all_perpetuals.py

# SDK 版本
uv run learning_examples/01_websockets/realtime_all_perpetuals_sdk.py
```

## 性能对比

| 特性 | 原始 WebSocket | SDK WebSocket |
|------|---------------|---------------|
| 代码行数 | 163 行 | 150 行 |
| 启动时间 | 约 2 秒 | 约 2 秒 |
| 内存占用 | 相似 | 相似 |
| 重连机制 | 需手动实现 | SDK 自动处理 |
| 生产就绪 | 需额外开发 | 开箱即用 |

## 推荐使用场景

### 使用原始 WebSocket (`realtime_all_perpetuals.py`)
- 学习 WebSocket 协议和实时数据流
- 需要完全控制连接行为
- 调试 WebSocket 连接问题
- 实现自定义的连接管理逻辑

### 使用 SDK (`realtime_all_perpetuals_sdk.py`)
- 生产环境部署
- 快速开发原型
- 与 SDK 其他功能集成（如交易、账户查询）
- 不想处理底层 WebSocket 细节

## 监控的合约数量

两种实现方式都能监控**所有 202 个永续合约资产**（testnet），包括：
- 主流资产：BTC, ETH, SOL, DOGE, AVAX 等
- 长尾资产：0G, 2Z, ANIME, AIXBT 等
- 总计 202 个资产的实时价格更新

## 注意事项

1. **环境变量**: 两个脚本都包含默认配置，无需设置环境变量即可运行
2. **网络延迟**: 实时价格更新延迟通常 < 50ms
3. **数据量**: 每秒可能接收数百次价格更新
4. **资源消耗**: 长时间运行建议监控内存使用情况
