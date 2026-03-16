# 数据服务 API 文档

## 概述

数据服务支持**按需从 Tushare 下载**，当策略请求数据时：

1. 先检查本地是否有数据
2. 如果本地数据完整，直接返回（0 API 调用）
3. 如果数据缺失，自动从 Tushare 下载缺失部分
4. 如果完全没有，下载整个请求范围

---

## API 端点

### GET `/api/data/price/{stock_code}`

获取股票价格数据（支持按需下载）

**参数：**
- `stock_code` (路径参数): 股票代码，如 `000001.SZ`
- `start_date` (查询参数): 开始日期，格式 `YYYY-MM-DD`
- `end_date` (查询参数): 结束日期，格式 `YYYY-MM-DD`
- `auto_download` (查询参数): 是否自动下载，默认 `true`

**请求示例：**
```bash
# 获取平安银行 2026 年数据（自动下载）
curl "http://localhost:5000/api/data/price/000001.SZ?start_date=2026-01-01&end_date=2026-03-16"

# 仅使用本地数据（不下载）
curl "http://localhost:5000/api/data/price/000001.SZ?auto_download=false"
```

**响应示例：**
```json
{
  "success": true,
  "message": "OK",
  "data": [
    {
      "ts_code": "000001.SZ",
      "trade_date": "20260102",
      "open": 10.50,
      "high": 10.85,
      "low": 10.45,
      "close": 10.80,
      "vol": 123456.78,
      "amount": 1234567.89
    },
    ...
  ]
}
```

**响应字段说明：**
| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | string | 股票代码 |
| trade_date | string | 交易日期（YYYYMMDD） |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| vol | float | 成交量（手） |
| amount | float | 成交额（元） |

---

### GET `/api/data/stocks`

获取股票列表（从本地股票池）

**请求示例：**
```bash
curl http://localhost:5000/api/data/stocks
```

**响应示例：**
```json
{
  "success": true,
  "message": "OK",
  "data": [
    "000001.SZ",
    "000002.SZ",
    "600519.SH",
    ...
  ]
}
```

---

### GET `/api/data/features/{stock_code}`

获取特征数据（含技术指标）

**请求示例：**
```bash
curl "http://localhost:5000/api/data/features/000001.SZ?start_date=2026-01-01&end_date=2026-03-16"
```

**响应：** 同 `/api/data/price`，目前返回价格数据（未来可扩展技术指标）

---

### GET `/api/data/stats`

获取数据统计信息

**请求示例：**
```bash
curl http://localhost:5000/api/data/stats
```

**响应示例：**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "total_stocks": 500,        // 股票池总数
    "feature_files": 50,        // 已下载的股票数
    "total_size_mb": 125.5,     // 总大小（MB）
    "coverage": 0.10            // 覆盖率（10%）
  }
}
```

---

### GET `/api/data/files`

获取数据文件列表

**请求示例：**
```bash
curl http://localhost:5000/api/data/files
```

**响应示例：**
```json
{
  "success": true,
  "message": "OK",
  "data": [
    {
      "path": "shared/data/features/000001_SZ.parquet",
      "name": "000001_SZ.parquet",
      "size": 2048576,
      "modified": "2026-03-16T13:00:00",
      "type": "parquet"
    },
    ...
  ]
}
```

---

## 按需下载行为

### 场景对比

| 场景 | 本地数据 | 请求范围 | 操作 | API 调用 |
|------|---------|---------|------|---------|
| 首次请求 | 无 | 2026-01-01 ~ 2026-03-16 | 下载整个范围 | 1 次 |
| 增量更新 | 2026-01-01 ~ 2026-03-10 | 2026-01-01 ~ 2026-03-16 | 下载 03-11 ~ 03-16 | 1 次 |
| 数据完整 | 2025-01-01 ~ 2026-03-16 | 2026-01-01 ~ 2026-03-16 | 直接返回 | 0 次 |
| 禁用下载 | 无 | 任意 | 返回错误 | 0 次 |

---

## 错误处理

### 错误 404：数据不存在

```json
{
  "detail": "股票数据不存在：000001.SZ"
}
```

**原因：**
- 本地无数据且 `auto_download=false`
- 本地无数据且 Tushare 下载失败（如 Token 无效）

**解决：**
1. 设置 `auto_download=true`（默认）
2. 配置有效的 Tushare Token
3. 检查股票代码是否正确

---

### 错误 500：内部错误

```json
{
  "detail": "获取价格数据失败：[详细错误信息]"
}
```

**可能原因：**
- Tushare API 错误
- 数据文件格式错误
- 磁盘空间不足

**解决：** 查看后端日志

---

## 使用示例

### Python 客户端

```python
import requests

API_BASE = "http://localhost:5000"

def get_stock_data(stock_code, start_date, end_date):
    """获取股票数据（自动按需下载）"""
    url = f"{API_BASE}/api/data/price/{stock_code}"
    params = {
        'start_date': start_date,
        'end_date': end_date
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    result = response.json()
    if result['success']:
        return result['data']
    else:
        raise Exception(result.get('message', 'Unknown error'))

# 使用示例
data = get_stock_data("000001.SZ", "2026-01-01", "2026-03-16")
print(f"获取到 {len(data)} 条记录")
```

### 批量获取

```python
def get_multiple_stocks(stock_list, start_date, end_date):
    """批量获取多只股票数据"""
    import asyncio
    import aiohttp
    
    async def fetch(session, stock):
        url = f"{API_BASE}/api/data/price/{stock}"
        params = {'start_date': start_date, 'end_date': end_date}
        
        async with session.get(url, params=params) as resp:
            result = await resp.json()
            return stock, result.get('data', [])
    
    async def main():
        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, stock) for stock in stock_list]
            results = await asyncio.gather(*tasks)
            return dict(results)
    
    return asyncio.run(main())

# 使用示例
stocks = ["000001.SZ", "600519.SH", "300750.SZ"]
data = get_multiple_stocks(stocks, "2026-01-01", "2026-03-16")

for stock, df in data.items():
    print(f"{stock}: {len(df)} 条记录")
```

---

## 性能建议

### 1. 批量请求

```python
# 推荐：一次请求获取长时间范围
get_stock_data("000001.SZ", "2026-01-01", "2026-03-16")

# 不推荐：多次请求短时间范围
get_stock_data("000001.SZ", "2026-01-01", "2026-01-31")
get_stock_data("000001.SZ", "2026-02-01", "2026-02-28")
get_stock_data("000001.SZ", "2026-03-01", "2026-03-16")
```

### 2. 使用缓存

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_data(stock_code, start_date, end_date):
    return get_stock_data(stock_code, start_date, end_date)

# 第二次调用直接返回缓存，不请求 API
data1 = get_cached_data("000001.SZ", "2026-01-01", "2026-03-16")
data2 = get_cached_data("000001.SZ", "2026-01-01", "2026-03-16")  # 缓存命中
```

### 3. 并发控制

```python
# 限制并发数，避免触发 Tushare 限流
semaphore = asyncio.Semaphore(5)  # 最多 5 个并发

async def fetch_with_limit(session, stock):
    async with semaphore:
        return await fetch(session, stock)
```

---

## 监控

### 查看下载统计

```bash
# 查看已下载的股票数量
curl http://localhost:5000/api/tushare/status

# 查看数据文件列表
curl http://localhost:5000/api/data/files
```

### 日志监控

后端日志会记录每次下载行为：

```
[Tushare] 按需获取数据：000001.SZ，范围 20260101-20260316
[Tushare] 本地无数据：000001.SZ，需要下载 20260101-20260316
[Tushare] 下载完成：000001.SZ，新增 52 条，共 52 条
```

---

## 相关文档

- [Tushare 集成指南](./TUSHARE_SETUP.md)
- [按需更新策略](./ON_DEMAND_UPDATE.md)
