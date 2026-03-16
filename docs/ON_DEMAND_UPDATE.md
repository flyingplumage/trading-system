# 按需数据更新策略

## 设计理念

**核心原则：** 只在策略需要时才下载数据，避免不必要的 API 调用和存储浪费。

### 传统方案 vs 按需方案

| 方案 | 更新策略 | 优点 | 缺点 |
|------|---------|------|------|
| **批量更新** | 定期更新所有股票 | 数据完整 | 浪费 API 配额，下载大量无用数据 |
| **按需更新** | 策略需要时才下载 | 节省资源，精准高效 | 首次请求稍慢 |

---

## 工作流程

```
策略请求数据
    ↓
检查本地数据库
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   无本地数据    │  部分数据缺失   │   数据完整      │
│                 │                 │                 │
│   下载整个范围   │  增量下载缺失   │   直接返回      │
│                 │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
    ↓
合并数据并保存
    ↓
返回给策略
```

---

## API 使用

### 1. 通过数据服务 API

```python
from app.services.data import DataService

data_service = DataService()

# 自动按需下载（默认）
df = data_service.get_price_data(
    stock_code="000001.SZ",
    start_date="2026-01-01",
    end_date="2026-03-16",
    auto_download=True  # 启用按需下载
)

# 仅使用本地数据（不下载）
df = data_service.get_price_data(
    stock_code="000001.SZ",
    auto_download=False  # 禁用下载
)
```

### 2. 通过 REST API

```bash
# 获取股票数据（自动按需下载）
curl "http://localhost:5000/api/data/price/000001.SZ?start_date=2026-01-01&end_date=2026-03-16"

# 响应示例
{
  "success": true,
  "data": [
    {"trade_date": "2026-01-02", "open": 10.5, "close": 10.8, ...},
    {"trade_date": "2026-01-03", "open": 10.8, "close": 10.6, ...},
    ...
  ]
}
```

---

## 智能判断逻辑

### 场景 1：本地无数据

```
请求：000001.SZ, 2026-01-01 ~ 2026-03-16
本地：无文件
操作：下载整个范围（2026-01-01 ~ 2026-03-16）
结果：保存 000001_SZ.parquet，返回请求范围数据
```

### 场景 2：数据部分过期

```
请求：000001.SZ, 2026-01-01 ~ 2026-03-16
本地：已有 2026-01-01 ~ 2026-03-10
操作：增量下载 2026-03-11 ~ 2026-03-16
结果：合并数据，新增 6 条记录
```

### 场景 3：数据完整

```
请求：000001.SZ, 2026-01-01 ~ 2026-03-16
本地：已有 2025-01-01 ~ 2026-03-16
操作：直接返回本地数据（不调用 API）
结果：0 API 调用，毫秒级响应
```

---

## 策略集成示例

### 策略训练时

```python
# 策略需要训练数据
def prepare_training_data(strategy_config):
    data_service = DataService()
    
    # 获取股票池（策略配置的）
    stock_list = strategy_config.get('stocks', ['000001.SZ'])
    
    # 获取回测时间段
    start_date = strategy_config.get('start_date', '2025-01-01')
    end_date = strategy_config.get('end_date', '2026-03-16')
    
    # 按需获取每只股票的数据
    data_dict = {}
    for stock in stock_list:
        df = data_service.get_price_data(
            stock_code=stock,
            start_date=start_date,
            end_date=end_date
        )
        data_dict[stock] = df
    
    return data_dict
```

### 实时交易时

```python
# 每日收盘后更新策略用到的股票
def update_strategy_stocks(strategy_list):
    data_service = DataService()
    today = datetime.now().strftime('%Y-%m-%d')
    
    for strategy in strategy_list:
        # 只更新策略持仓的股票
        for stock in strategy['holdings']:
            # 获取最近 5 天数据（防止遗漏）
            start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            
            df = data_service.get_price_data(
                stock_code=stock,
                start_date=start_date,
                end_date=today
            )
            print(f"更新 {stock}: {len(df)} 条记录")
```

---

## 性能优化

### 1. 批量请求优化

```python
# 推荐：批量获取多只股票
async def get_multiple_stocks(stock_list, start_date, end_date):
    data_service = DataService()
    
    # 并发请求（限制并发数）
    semaphore = asyncio.Semaphore(5)  # 最多 5 个并发
    
    async def fetch_with_limit(stock):
        async with semaphore:
            return data_service.get_price_data(stock, start_date, end_date)
    
    tasks = [fetch_with_limit(stock) for stock in stock_list]
    results = await asyncio.gather(*tasks)
    
    return dict(zip(stock_list, results))
```

### 2. 缓存策略

```python
# 内存缓存（避免重复下载）
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_data(stock_code, start_date, end_date):
    data_service = DataService()
    return data_service.get_price_data(stock_code, start_date, end_date)
```

---

## 监控与日志

### 下载统计

```bash
# 查看数据状态
curl http://localhost:5000/api/tushare/status

# 响应
{
  "total_stocks": 500,      # 股票池总数
  "feature_files": 50,      # 已下载的股票数
  "total_records": 15000,   # 总记录数
  "coverage": "10%"         # 覆盖率
}
```

### 日志示例

```
[Tushare] 按需获取数据：000001.SZ，范围 20260101-20260316
[Tushare] 本地无数据：000001.SZ，需要下载 20260101-20260316
[Tushare] 获取日线数据：000001.SZ
[Tushare] 获取到 52 条记录
[Tushare] 下载完成：000001.SZ，新增 52 条，共 52 条

# 第二次请求（数据已存在）
[Tushare] 按需获取数据：000001.SZ，范围 20260101-20260316
[Tushare] 数据已覆盖：000001.SZ，本地范围 20260101-20260316
[DataService] 使用本地数据：000001.SZ，共 52 条
```

---

## 最佳实践

### ✅ 推荐

1. **策略启动前预加载** - 在策略初始化时批量获取数据
2. **定期更新持仓股票** - 每天收盘后更新策略用到的股票
3. **设置合理的时间范围** - 不要请求过长的历史数据
4. **监控 API 使用量** - 避免超出 Tushare 限制

### ❌ 避免

1. **频繁请求相同数据** - 使用缓存
2. **一次性获取全量数据** - 按需获取
3. **忽略错误处理** - 下载失败时要有降级方案
4. **无限制并发** - 控制并发数，避免触发限流

---

## 配置示例

### 策略配置文件

```yaml
# configs/my_strategy.yaml
strategy:
  name: "momentum_iris"
  stocks:
    - "000001.SZ"
    - "600519.SH"
    - "300750.SZ"
  
  data:
    # 数据获取配置
    auto_download: true       # 启用按需下载
    start_date: "2025-01-01"  # 回测开始日期
    end_date: "2026-03-16"    # 回测结束日期
    update_frequency: "daily" # 更新频率
  
  tushare:
    # 覆盖全局 Tushare 配置
    token: "${TUSHARE_TOKEN}"
    rate_limit: 500
```

---

## 故障排查

### 问题 1：下载失败

```
NotFoundError: 股票数据不存在且无法下载：000001.SZ
```

**原因：**
- Tushare Token 无效
- 股票代码错误
- API 限流

**解决：**
```bash
# 检查 Token
echo $TUSHARE_TOKEN

# 验证股票代码
curl http://localhost:5000/api/tushare/pool

# 检查 API 状态
curl http://localhost:5000/api/tushare/status
```

### 问题 2：数据不完整

```
警告：本地数据范围 20260101-20260310，请求范围 20260101-20260316
```

**原因：** 周末或节假日无交易数据

**解决：** 这是正常的，A 股周末休市

---

## 总结

按需更新策略的核心优势：

1. **节省 API 配额** - 只下载策略需要的数据
2. **减少存储占用** - 不存储无用股票数据
3. **提高响应速度** - 本地数据毫秒级返回
4. **自动化维护** - 智能判断是否需要更新

**适用场景：**
- 策略数量少，股票池小
- API 配额有限
- 需要频繁更新数据

**不适用场景：**
- 需要全市场数据回测
- 策略频繁切换股票池
- 对首次请求延迟敏感
