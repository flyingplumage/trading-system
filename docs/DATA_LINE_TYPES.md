# K 线数据类型说明

## 概述

系统支持两种主要的 K 线数据类型：

| 类型 | 周期 | 适用场景 | 数据量 | Tushare 权限 |
|------|------|---------|--------|-------------|
| **日线** | 1 天 | 中长线策略、基础训练 | 少 | 免费 |
| **分钟线** | 1/5/15/30/60 分钟 | 短线交易、高频策略 | 多 | 需要积分 |

---

## 日线数据

### 特点

- **数据量小** - 一年约 250 条记录
- **适合训练** - RL 智能体容易学习长期模式
- **免费获取** - Tushare 基础权限即可
- **更新频率** - 每日盘后更新一次

### 字段说明

```python
{
    'ts_code': '000001.SZ',      # 股票代码
    'trade_date': '20260316',     # 交易日期
    'open': 10.50,                # 开盘价
    'high': 10.85,                # 最高价
    'low': 10.45,                 # 最低价
    'close': 10.80,               # 收盘价
    'vol': 123456.78,             # 成交量（手）
    'amount': 1234567.89          # 成交额（元）
}
```

### 使用示例

```python
from app.services.tushare_service import get_tushare_service

tushare = get_tushare_service()

# 获取日线数据
df = tushare.get_daily_data(
    ts_code='000001.SZ',
    start_date='20260101',
    end_date='20260316'
)

print(f"获取到 {len(df)} 条日线数据")
```

### 训练配置

```bash
# 日线训练（推荐）
curl -X POST http://localhost:5000/api/train/start \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "daily_momentum",
    "env_name": "momentum",
    "stock_code": "000001.SZ",
    "steps": 10000,
    "data_type": "daily"
  }'
```

---

## 分钟线数据

### 特点

- **数据量大** - 一天 240 条（1 分钟线）
- **适合短线** - 捕捉日内交易机会
- **需要权限** - Tushare 需要一定积分
- **更新频率** - 实时更新

### 可用周期

| 周期代码 | 说明 | 每天条数 |
|---------|------|---------|
| `1` | 1 分钟 | 240 条 |
| `5` | 5 分钟 | 48 条 |
| `15` | 15 分钟 | 16 条 |
| `30` | 30 分钟 | 8 条 |
| `60` | 60 分钟 | 4 条 |

### 字段说明

```python
{
    'ts_code': '000001.SZ',      # 股票代码
    'trade_time': '2026-03-16 10:30:00',  # 交易时间
    'open': 10.52,               # 开盘价
    'high': 10.55,               # 最高价
    'low': 10.50,                # 最低价
    'close': 10.53,              # 收盘价
    'vol': 1234.56,              # 成交量（手）
    'amount': 12345.67           # 成交额（元）
}
```

### 使用示例

```python
from app.services.tushare_service import get_tushare_service

tushare = get_tushare_service()

# 获取 5 分钟线数据
df = tushare.get_min_data(
    ts_code='000001.SZ',
    freq='5',  # 5 分钟
    start_date='20260316 09:30:00',
    end_date='20260316 15:00:00'
)

print(f"获取到 {len(df)} 条分钟线数据")
```

### 训练配置

```bash
# 分钟线训练（需要权限）
curl -X POST http://localhost:5000/api/train/start \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "min5_breakout",
    "env_name": "breakout",
    "stock_code": "000001.SZ",
    "data_type": "min",
    "freq": "5",
    "steps": 50000
  }'
```

---

## 推荐方案

### 方案 1：日线为主（当前权限）

**适用：** Tushare 免费用户

```yaml
# 训练配置
training:
  data_type: daily
  stocks:
    - "000001.SZ"
    - "600519.SH"
  
  # 日线训练参数
  steps: 10000          # 训练步数
  window_size: 20       # 观察 20 天
  initial_cash: 1000000
```

**优点：**
- ✅ 数据获取稳定
- ✅ 训练速度快
- ✅ 模型容易收敛

**缺点：**
- ❌ 无法捕捉日内机会
- ❌ 交易频率低

---

### 方案 2：日线 + 分钟线混合

**适用：** 有分钟线权限

```yaml
# 训练配置
training:
  # 第一阶段：日线预训练
  stage1:
    data_type: daily
    steps: 5000
    purpose: "学习长期趋势"
  
  # 第二阶段：分钟线微调
  stage2:
    data_type: min
    freq: 5
    steps: 20000
    purpose: "学习日内交易"
```

**优点：**
- ✅ 结合长短期模式
- ✅ 策略更稳健

**缺点：**
- ❌ 需要较高权限
- ❌ 训练时间长

---

### 方案 3：纯分钟线（高频）

**适用：** 专业高频交易

```yaml
# 训练配置
training:
  data_type: min
  freq: 1  # 1 分钟线
  
  # 高频训练参数
  steps: 100000
  window_size: 60   # 观察 60 分钟
  commission_rate: 0.0005  # 更高手续费
```

**优点：**
- ✅ 捕捉所有波动
- ✅ 交易机会多

**缺点：**
- ❌ 数据量巨大
- ❌ 训练困难
- ❌ 手续费敏感

---

## 数据存储

### 目录结构

```
backend/shared/data/
├── features/              # 日线数据
│   ├── 000001_SZ.parquet
│   └── 600519_SH.parquet
├── min_data/              # 分钟线数据
│   ├── 1min/
│   │   ├── 000001_SZ.parquet
│   │   └── ...
│   ├── 5min/
│   │   └── ...
│   └── 15min/
└── pool/
    └── stock_pool.yaml
```

### 数据格式

**日线数据：**
```python
df.columns = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']
df['trade_date'] = pd.to_datetime()  # datetime64
```

**分钟线数据：**
```python
df.columns = ['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount']
df['trade_time'] = pd.to_datetime()  # datetime64
```

---

## 增量更新策略

### 日线更新

```python
# 每天盘后执行一次
tushare.incremental_update('000001.SZ')
# 自动判断最后更新日期，只下载新数据
```

**更新频率：** 每日 16:00 后

**API 消耗：** 1 次/股票

---

### 分钟线更新

```python
# 每小时执行一次
tushare.get_min_data(
    ts_code='000001.SZ',
    freq='5',
    start_date='20260316 14:00:00',
    end_date='20260316 15:00:00'
)
```

**更新频率：** 每小时或实时

**API 消耗：** 较高，建议缓存

---

## 性能对比

| 指标 | 日线 | 5 分钟线 | 1 分钟线 |
|------|------|---------|---------|
| 年数据量 | 250 条 | 60,000 条 | 300,000 条 |
| 训练速度 | 快 | 中 | 慢 |
| 内存占用 | 低 | 中 | 高 |
| 策略频率 | 低频 | 中频 | 高频 |
| API 消耗 | 低 | 中 | 高 |

---

## 最佳实践

### 1. 日线训练（推荐起步）

```bash
# 使用日线数据训练动量策略
curl -X POST http://localhost:5000/api/train/start \
  -d '{
    "strategy": "momentum_daily",
    "env_name": "momentum",
    "stock_code": "000001.SZ",
    "steps": 10000
  }'
```

### 2. 多股票训练

```python
# 批量训练多个股票
stocks = ['000001.SZ', '600519.SH', '300750.SZ']

for stock in stocks:
    trainer.train(
        strategy='universal',
        stock_code=stock,
        steps=5000
    )
```

### 3. 数据预加载

```python
# 训练前预加载数据
df = data_service.get_price_data(
    stock_code='000001.SZ',
    start_date='2025-01-01',
    end_date='2026-03-16',
    auto_download=True
)
```

---

## 故障排查

### 问题 1：分钟线数据获取失败

```
[Tushare] 获取分钟线失败：抱歉，您没有权限访问该接口
```

**解决：**
- 检查 Tushare 积分是否足够
- 使用日线数据替代
- 申请开通权限

### 问题 2：数据量不足

```
AssertionError: 数据量不足
```

**解决：**
- 增加数据时间范围
- 减小 `window_size` 参数
- 检查股票是否停牌

### 问题 3：训练不收敛

**可能原因：**
- 分钟线噪声太大
- 学习率过高
- 环境奖励设计不合理

**解决：**
- 改用日线数据
- 降低学习率（1e-5）
- 调整奖励函数

---

## 相关文档

- [Tushare 集成指南](./TUSHARE_SETUP.md)
- [交易环境系统](./TRADING_ENVIRONMENTS.md)
- [训练 API 文档](./TRAINING_API.md)
