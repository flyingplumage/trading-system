# 交易环境系统

## 概述

交易环境是 RL 智能体训练的核心，定义了：
- **市场交互规则** - 如何下单、成交
- **奖励函数** - 什么行为是好的
- **观察空间** - 智能体能看到什么信息

---

## 内置环境

系统提供 3 个示例环境，用于演示和测试：

### 1. **动量策略环境** (`momentum`)

**策略逻辑：** 追涨杀跌

**特征：**
- ROC (Rate of Change) - 价格变化率
- RSI (Relative Strength Index) - 相对强弱指标
- 价格相对于 MA20 的位置
- 成交量变化率
- 5 日价格动量

**奖励函数：**
- ✅ 持仓时价格上涨
- ✅ 动量一致操作（上涨买入、下跌卖出）
- ❌ 交易成本
- ❌ 错误操作（追高杀跌）

**适用场景：** 趋势明显的股票

---

### 2. **均值回归环境** (`mean_reversion`)

**策略逻辑：** 低买高卖

**特征：**
- 布林带上下轨位置
- RSI
- 价格偏离均线程度
- 布林带宽度（波动率）

**奖励函数：**
- ✅ 低于下轨买入
- ✅ 高于上轨卖出
- ✅ 价格向均值回归
- ❌ 追涨杀跌

**适用场景：** 震荡市、波动稳定的股票

---

### 3. **突破策略环境** (`breakout`)

**策略逻辑：** 突破关键价位

**特征：**
- 价格相对于 N 日高点/低点
- ATR (波动率)
- 突破强度
- 成交量突破

**奖励函数：**
- ✅ 向上突破买入
- ✅ 向下突破卖出
- ✅ 趋势延续
- ❌ 假突破

**适用场景：** 突破形态明显的股票

---

## API 使用

### 查看可用环境

```bash
curl http://localhost:5000/api/environments
```

**响应：**
```json
{
  "success": true,
  "data": [
    {"name": "momentum", "class": "MomentumEnv", "description": "动量策略环境"},
    {"name": "mean_reversion", "class": "MeanReversionEnv", "description": "均值回归策略环境"},
    {"name": "breakout", "class": "BreakoutEnv", "description": "突破策略环境"}
  ]
}
```

### 查看环境详情

```bash
curl http://localhost:5000/api/environments/momentum
```

---

## 训练配置

### 通过 API 训练

```bash
curl -X POST http://localhost:5000/api/train/start \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "my_momentum_strategy",
    "steps": 50000,
    "env_name": "momentum",
    "stock_code": "000001.SZ",
    "learning_rate": 3e-5
  }'
```

### Python 代码训练

```python
from app.services.trainer import trainer

trainer.train(
    strategy="my_strategy",
    exp_id="exp_001",
    task_id=1,
    steps=50000,
    env_name="momentum",      # 环境选择
    stock_code="000001.SZ",   # 训练标的
    learning_rate=3e-5
)
```

---

## 自定义环境

### 方式 1：继承基类

```python
from app.env.base import TradingEnvBase
import numpy as np

class MyCustomEnv(TradingEnvBase):
    """自定义策略环境"""
    
    def __init__(self, df, **kwargs):
        super().__init__(df, **kwargs)
        # 自定义参数
    
    def _calculate_features(self, window_data):
        """自定义特征"""
        # 计算你的特征
        features = []
        # ...
        return np.array(features)
    
    def _calculate_reward(self, action, current_price):
        """自定义奖励"""
        reward = 0.0
        # 你的奖励逻辑
        return reward

# 注册环境
from app.env import BUILTIN_ENVS
BUILTIN_ENVS['my_custom'] = MyCustomEnv
```

### 方式 2：策略 Pipeline 上传（推荐）

用户可以将完整的环境代码打包上传：

```python
# strategy_pipeline.py
from app.env.base import TradingEnvBase

class MyStrategyEnv(TradingEnvBase):
    # ... 完整的环境实现

# 训练时指定
trainer.train(
    strategy="user_uploaded",
    env_class=MyStrategyEnv,  # 使用上传的环境
    ...
)
```

---

## 环境参数

### 通用参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `initial_cash` | 1,000,000 | 初始资金 |
| `commission_rate` | 0.0003 | 手续费率（万分之三） |
| `slippage` | 0.001 | 滑点（0.1%） |
| `window_size` | 20 | 观察窗口大小 |

### 环境特定参数

**动量环境：**
- `momentum_window`: 动量计算窗口（默认 10）

**均值回归环境：**
- `bb_window`: 布林带窗口（默认 20）
- `bb_std`: 布林带标准差倍数（默认 2.0）

**突破环境：**
- `breakout_window`: 突破检测窗口（默认 20）
- `atr_window`: ATR 计算窗口（默认 14）

---

## 交易规则

### 动作空间

| 动作 | 值 | 说明 |
|------|-----|------|
| 持有/观望 | 0 | 保持当前仓位 |
| 买入 | 1 | 全仓买入 |
| 卖出 | 2 | 全部卖出 |

### 成交规则

- **买入**：使用现金全仓买入，考虑手续费和滑点
- **卖出**：卖出全部持仓，考虑手续费和滑点
- **平仓**：T+0（当前简化实现）

### 终止条件

- 现金 <= 0（破产）
- 组合价值 < 初始资金 50%（大额亏损）
- 数据结束

---

## 绩效指标

训练完成后，环境会计算以下指标：

| 指标 | 说明 |
|------|------|
| `total_return` | 总收益率 |
| `annual_return` | 年化收益率 |
| `sharpe_ratio` | 夏普比率 |
| `max_drawdown` | 最大回撤 |
| `n_trades` | 交易次数 |

---

## 最佳实践

### 1. 选择合适的環境

| 市场环境 | 推荐环境 |
|---------|---------|
| 上涨趋势 | `momentum` |
| 震荡市 | `mean_reversion` |
| 突破形态 | `breakout` |

### 2. 参数调优

```python
# 不同学习率测试
for lr in [1e-5, 3e-5, 1e-4]:
    trainer.train(
        strategy=f"test_lr_{lr}",
        learning_rate=lr,
        ...
    )
```

### 3. 多环境训练

```python
# 在多个股票上训练
for stock in stock_pool:
    trainer.train(
        strategy="universal",
        stock_code=stock,
        ...
    )
```

---

## 日志示例

```
[Trainer] 开始训练 - 策略：my_momentum, 环境：momentum, 步数：50000
[Trainer] 获取股票数据：000001.SZ
[Trainer] 获取到 252 条数据
[Trainer] 创建交易环境：momentum
[Trainer] 创建 PPO 模型，学习率：3e-05
[Trainer] 开始训练，总步数：50000
[Trainer] 进度：2.0%, 步数：1000/50000, 组合价值：1005000.00, 耗时：0.5 分钟
[Trainer] 进度：4.0%, 步数：2000/50000, 组合价值：1012000.00, 耗时：1.0 分钟
...
[Trainer] 训练完成，总步数：50000
[Trainer] 模型已保存：shared/models/my_momentum_exp_001.zip
```

---

## 故障排查

### 问题 1：环境创建失败

```
ValueError: 未知环境：custom_env
```

**解决：** 确认环境已注册或上传

### 问题 2：数据不足

```
AssertionError: 数据量不足
```

**解决：** 增加数据时间范围或减小 `window_size`

### 问题 3：训练不收敛

**可能原因：**
- 奖励函数设计不合理
- 学习率过高/过低
- 环境噪声太大

**解决：**
- 调整奖励函数权重
- 尝试不同学习率
- 增加训练步数

---

## 相关文档

- [训练系统 API](./TRAINING_API.md)
- [策略开发指南](./STRATEGY_DEVELOPMENT.md)
- [Tushare 数据集成](./TUSHARE_SETUP.md)
