# 量化交易系统 - 存储架构说明

**更新时间：** 2026-03-21

---

## 📊 存储架构概览

```
量化交易系统存储架构
│
├── 🗄️ 数据库层 (SQLite)
│   └── qframe.db - 元数据管理
│
├── 📁 文件存储层
│   ├── shared/data/features/ - 特征数据 (Parquet)
│   ├── shared/data/raw/ - 原始数据
│   ├── shared/data/pool/ - 股票池配置
│   └── shared/models/ - 模型文件
│
├── 📝 日志层
│   ├── data/checkpoints/ - 训练检查点
│   └── logs/ - 系统日志
│
└── 🔧 配置层
    ├── .env - 环境变量
    └── configs/ - 配置文件
```

---

## 1️⃣ 数据库层 (SQLite)

**位置：** `backend/data/qframe.db`  
**模式：** WAL (Write-Ahead Logging)  
**大小：** ~45KB

### 表结构

| 表名 | 用途 | 记录数 |
|------|------|--------|
| `experiments` | 实验管理 | 4 |
| `models` | 模型注册 | 3 |
| `training_tasks` | 训练任务队列 | 3 |

### experiments 表
```sql
CREATE TABLE experiments (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    strategy VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    config TEXT,              -- JSON 配置
    metrics TEXT,             -- JSON 指标
    result TEXT,              -- JSON 结果
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### models 表
```sql
CREATE TABLE models (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    strategy VARCHAR(128) NOT NULL,
    version INTEGER,
    experiment_id VARCHAR(64),
    model_path VARCHAR(512),  -- 模型文件路径
    performance TEXT,         -- JSON 性能指标
    created_at TIMESTAMP
);
```

### training_tasks 表
```sql
CREATE TABLE training_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy VARCHAR(128) NOT NULL,
    steps INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    experiment_id VARCHAR(64),
    result TEXT,
    error TEXT,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 数据库优化配置
```python
PRAGMA journal_mode=WAL      # WAL 模式，支持并发读
PRAGMA synchronous=NORMAL    # 平衡性能与安全
PRAGMA cache_size=-64000     # 64MB 缓存
PRAGMA foreign_keys=ON       # 外键约束
```

---

## 2️⃣ 文件存储层

### 2.1 特征数据 (Parquet)

**位置：** `backend/shared/data/features/`  
**格式：** Apache Parquet (列式存储)  
**压缩：** Snappy

| 文件 | 大小 | 记录数 | 说明 |
|------|------|--------|------|
| 000001_SZ.parquet | 27KB | 125 | 平安银行 |
| 000002_SZ.parquet | 10KB | 61 | 万科 A |
| 600000_SH.parquet | 10KB | 61 | 浦发银行 |
| 600519_SH.parquet | 10KB | 61 | 贵州茅台 |

**数据字段:**
```
ts_code, trade_date, open, high, low, close,
pre_close, change, pct_chg, vol, amount
```

**存储估算:**
- 单只股票/年：~100KB (252 个交易日)
- 1000 只股票/年：~100MB
- 支持 10 年历史：~1GB

### 2.2 原始数据

**位置：** `backend/shared/data/raw/`  
**用途：** Tushare API 原始响应数据  
**状态：** 当前为空 (直接保存为 features)

### 2.3 股票池配置

**位置：** `backend/shared/data/pool/stock_pool.yaml`

```yaml
stocks:
  - 000001.SZ  # 平安银行
  - 000002.SZ  # 万科 A
  - 600000.SH  # 浦发银行
  - 600519.SH  # 贵州茅台
  # ...

sectors:
  - 银行
  - 房地产
  - 白酒
```

### 2.4 模型文件

**位置：** `backend/shared/models/`  
**格式：** ZIP (Stable Baselines3 模型)

| 文件 | 大小 | 说明 |
|------|------|------|
| ppo_test_*.zip | 140KB | PPO 测试模型 |

**模型结构:**
```
ppo_{exp_id}.zip
├── data/           # 模型参数
├── policy.pkl      # 策略网络
└── pytorch_model.bin
```

**存储估算:**
- 单模型大小：~140KB
- 100 个模型：~14MB
- 建议定期清理旧模型

---

## 3️⃣ 日志层

### 3.1 训练检查点

**位置：** `backend/data/checkpoints/`  
**用途：** 训练中断恢复  
**当前状态：** 空 (训练步数少，无需检查点)

### 3.2 系统日志

**位置：** `logs/`  
**日志文件:**
- `backend.log` - 后端服务日志
- `training.log` - 训练日志
- `backtest.log` - 回测日志

---

## 4️⃣ 配置层

### 4.1 环境变量

**位置：** `backend/.env`

```bash
# Tushare API Token
TUSHARE_TOKEN=a184c315fd031d9adc136b0c6519aa481bffc281c1ae114f77a25beb

# 数据库配置
DATABASE_URL=sqlite:///data/qframe.db

# API 服务配置
API_HOST=0.0.0.0
API_PORT=5000

# JWT Secret
JWT_SECRET=your_jwt_secret_change_this_in_production
```

### 4.2 配置文件

**位置：** `backend/configs/`

---

## 📈 存储性能

### 读写速度

| 操作 | 速度 | 说明 |
|------|------|------|
| SQLite 查询 | <10ms | 元数据读取 |
| Parquet 读取 | <50ms | 单只股票数据 |
| Parquet 写入 | <100ms | 单只股票保存 |
| 模型加载 | <500ms | 140KB 模型 |
| 模型保存 | <1s | 训练完成 |

### 存储效率

| 数据类型 | 压缩率 | 说明 |
|----------|--------|------|
| Parquet | 10:1 | 列式存储 + Snappy |
| SQLite | 2:1 | WAL 模式 |
| 模型 ZIP | 3:1 | 默认压缩 |

---

## 🔒 数据安全

### 备份策略

1. **数据库备份**
   - WAL 文件自动保护
   - 建议定期备份 `qframe.db`

2. **模型备份**
   - 重要模型复制到 `shared/models/registered/`
   - 版本化管理

3. **数据备份**
   - Parquet 文件可重新下载
   - 建议备份股票池配置

### 并发控制

- SQLite WAL 模式支持多读单写
- 训练任务队列避免并发写入
- 文件锁防止并发写入同一股票

---

## 🚀 扩展方案

### 当前限制

| 组件 | 限制 | 影响 |
|------|------|------|
| SQLite | 单写多读 | 不适合高并发写入 |
| 本地存储 | 单机容量 | 大规模数据需分布式 |
| 无缓存 | 直接读文件 | 高频访问性能瓶颈 |

### 升级路径

1. **数据库升级** (10 万 + 实验)
   - PostgreSQL / MySQL
   - 支持分布式部署

2. **数据存储升级** (TB 级)
   - DuckDB (分析查询)
   - MinIO / S3 (对象存储)

3. **缓存层** (高频访问)
   - Redis (热点数据)
   - 内存数据库 (实时指标)

---

## 📊 当前存储用量

```
backend/
├── data/
│   ├── qframe.db          45KB
│   └── checkpoints/       0KB
├── shared/
│   ├── data/features/     95KB (6 只股票)
│   ├── data/raw/          0KB
│   ├── data/pool/         1KB
│   └── models/            420KB (3 个模型)
└── logs/                  ~1MB

总用量：~1.6MB
```

---

## ✅ 架构特点

### 优势
- ✅ 简单轻量，无需额外依赖
- ✅ SQLite 足够支持单机场景
- ✅ Parquet 高效压缩，适合时序数据
- ✅ 文件 + 数据库混合，灵活性好

### 劣势
- ❌ 不支持分布式部署
- ❌ 高并发写入性能有限
- ❌ 无数据冗余保护

### 适用场景
- ✅ 个人/小团队量化研究
- ✅ 单机训练和回测
- ✅ 1000 只股票以内
- ❌ 大规模生产环境 (需升级)

---

*文档生成时间：2026-03-21*
