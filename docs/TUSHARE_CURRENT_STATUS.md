# Tushare 接口权限现状

## 当前 Token 权限

**Token:** `a184c315fd031d9adc136b0c6519aa481bffc281c1ae114f77a25beb`

**权限等级：** 基础免费版

**限制：**
- 每小时最多访问 1 次
- 仅支持基础接口（日线、股票列表等）
- 不支持分钟线、资金流等高级接口

---

## 支持的接口

### ✅ 可用接口

| 接口名 | 功能 | 限制 |
|--------|------|------|
| `daily` | 日线行情 | 每小时 1 次 |
| `stock_basic` | 股票列表 | 每小时 1 次 |
| `trade_cal` | 交易日历 | 无限制 |

### ❌ 不支持接口

| 接口名 | 功能 | 需要权限 |
|--------|------|---------|
| `stk_min` | 分钟线 | 需要积分 |
| `min` | 分钟线 | 需要积分 |
| `moneyflow` | 资金流 | 需要积分 |
| `limit_list` | 涨跌停 | 需要积分 |

---

## 替代方案

### 方案 1：使用模拟分钟线数据

从日线数据生成模拟分钟线：

```python
import pandas as pd
import numpy as np

def generate_min_data(daily_df, freq='5min'):
    """
    从日线数据生成模拟分钟线
    
    原理：
    - 将每日 OHLC 分配到各分钟
    - 添加随机波动
    """
    min_data = []
    
    for date, row in daily_df.iterrows():
        # 生成日内分钟数据
        n_bars = 48 if freq == '5min' else 240
        
        # 简单分配
        opens = np.linspace(row['open'], row['close'], n_bars)
        highs = opens + np.random.uniform(0, 0.02) * opens
        lows = opens - np.random.uniform(0, 0.02) * opens
        closes = opens + np.random.uniform(-0.01, 0.01) * opens
        
        for i in range(n_bars):
            min_data.append({
                'ts_code': row['ts_code'],
                'trade_time': f"{row['trade_date']} {9+i//12}:{(i%12)*5:02d}:00",
                'open': opens[i],
                'high': highs[i],
                'low': lows[i],
                'close': closes[i],
                'vol': row['vol'] / n_bars
            })
    
    return pd.DataFrame(min_data)
```

---

### 方案 2：使用其他免费数据源

#### 1. Akshare（免费）

```python
import akshare as ak

# 获取分钟线数据
df = ak.stock_zh_a_hist_min_em(
    symbol="000001",
    period="5",
    adjust="qfq"
)
```

**优点：**
- 完全免费
- 支持分钟线
- 数据丰富

**缺点：**
- 稳定性较差
- 可能限流
- 数据质量参差不齐

---

#### 2. Baostock（免费）

```python
import baostock as bs

# 登录
lg = bs.login()

# 获取分钟线
rs = bs.query_history_k_data_plus(
    "sh.000001",
    "date,time,open,high,low,close,volume",
    frequency="5",
    start_date="2026-01-01"
)
```

**优点：**
- 免费
- 官方背景
- 数据稳定

**缺点：**
- 需要登录
- 分钟线数据有限

---

### 方案 3：升级 Tushare 会员

**价格：**
- 120 积分/年（约 120 元）
- 可获取分钟线权限

**升级后权限：**
- ✅ 5 分钟线
- ✅ 15 分钟线
- ✅ 60 分钟线
- ✅ 更多高级指标

**升级方法：**
1. 访问 https://tushare.pro/user/vip
2. 充值获取积分
3. 自动解锁对应权限

---

## 当前推荐方案

### 日线训练（立即可用）

```bash
# 使用日线数据训练
curl -X POST http://localhost:5000/api/train/start \
  -d '{
    "strategy": "daily_momentum",
    "env_name": "momentum",
    "stock_code": "000001.SZ",
    "steps": 10000
  }'
```

**优势：**
- ✅ 数据稳定
- ✅ 训练快速
- ✅ 模型易收敛
- ✅ 零成本

**适用策略：**
- 动量策略
- 均值回归
- 突破策略
- 趋势跟踪

---

### 分钟线训练（需要升级）

**选项 1：升级 Tushare**
- 成本：120 元/年
- 时间：即时可用
- 质量：高

**选项 2：使用 Akshare**
- 成本：免费
- 时间：需集成
- 质量：中

**选项 3：模拟数据**
- 成本：免费
- 时间：即时可用
- 质量：低（仅用于测试）

---

## 训练效果对比

| 数据源 | 训练速度 | 模型质量 | 成本 | 推荐度 |
|--------|---------|---------|------|--------|
| **日线** | 快 | 好 | 免费 | ⭐⭐⭐⭐⭐ |
| **5 分钟线** | 中 | 很好 | 120 元/年 | ⭐⭐⭐⭐ |
| **1 分钟线** | 慢 | 优秀 | 高 | ⭐⭐⭐ |
| **模拟分钟线** | 快 | 一般 | 免费 | ⭐⭐ |

---

## 结论

**当前建议：**

1. **使用日线数据训练** - 完全够用
   - 验证策略逻辑
   - 训练 RL 模型
   - 测试系统流程

2. **后续升级** - 根据需求
   - 策略需要分钟线时
   - 有预算时
   - 需要更高精度时

3. **备选方案** - Akshare
   - 免费分钟线
   - 作为补充数据源

---

## 代码示例

### 日线训练（当前可用）

```python
from app.services.trainer import trainer

trainer.train(
    strategy='momentum_daily',
    env_name='momentum',
    stock_code='000001.SZ',
    steps=10000,
    data_type='daily'  # 日线
)
```

### 分钟线训练（需要权限）

```python
# 需要 Tushare 升级后
trainer.train(
    strategy='breakout_5min',
    env_name='breakout',
    stock_code='000001.SZ',
    steps=50000,
    data_type='min',
    freq='5'  # 5 分钟线
)
```

---

## 相关文档

- [K 线数据类型](./DATA_LINE_TYPES.md)
- [Tushare 配置](./TUSHARE_SETUP.md)
- [训练系统 API](./TRAINING_API.md)
