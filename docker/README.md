# PostgreSQL Docker 部署指南

## 📦 快速启动

### 1. 安装 Docker (如未安装)

```bash
# Ubuntu 24.04
sudo apt update
sudo apt install -y docker.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl enable docker
sudo systemctl start docker

# 验证安装
docker --version
docker compose version
```

### 2. 启动 PostgreSQL

```bash
cd /root/.openclaw/workspace/projects/trading-system-release/docker

# 复制环境变量文件
cp .env.example .env

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f postgres
```

### 3. 验证服务

```bash
# 检查容器状态
docker compose ps

# 测试数据库连接
docker exec -it quant-postgres psql -U quant -d qframe -c "SELECT version();"
```

---

## 🔧 服务信息

| 服务 | 地址 | 账号 | 密码 |
|------|------|------|------|
| PostgreSQL | localhost:5432 | quant | quant_password_2024 |
| pgAdmin | http://localhost:5050 | admin@qframe.local | admin_password_2024 |

---

## 📊 数据库表结构

初始化脚本自动创建以下表：

- `experiments` - 实验跟踪
- `models` - 模型注册
- `training_tasks` - 训练任务队列
- `users` - 用户管理
- `api_keys` - API 密钥
- `stock_daily` - 股票日线行情（按月分区）
- `training_metrics` - 训练过程指标

---

## 🔌 应用连接配置

### FastAPI (SQLAlchemy)

```python
# .env
DATABASE_URL=postgresql://quant:quant_password_2024@localhost:5432/qframe

# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### FastAPI (Async)

```python
# .env
ASYNC_DATABASE_URL=postgresql+asyncpg://quant:quant_password_2024@localhost:5432/qframe

# app/db/database.py
from databases import Database

DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
database = Database(DATABASE_URL)

# 启动时连接
@app.on_event("startup")
async def startup():
    await database.connect()
```

---

## 🛠️ 常用命令

```bash
# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 进入数据库 CLI
docker exec -it quant-postgres psql -U quant -d qframe

# 备份数据
docker exec quant-postgres pg_dump -U quant qframe > backup.sql

# 恢复数据
docker exec -i quant-postgres psql -U quant -d qframe < backup.sql

# 清理所有数据（危险！）
docker compose down -v
```

---

## 📈 性能优化

`docker-compose.yml` 已配置以下 PostgreSQL 参数：

```yaml
max_connections=100        # 最大连接数
shared_buffers=256MB       # 共享缓冲区
effective_cache_size=768MB # 缓存大小估算
work_mem=16MB              # 单查询工作内存
maintenance_work_mem=128MB # 维护操作内存
```

根据服务器内存调整（推荐：shared_buffers = 物理内存的 25%）。

---

## 🔐 安全建议

**生产环境务必修改：**

1. 修改 `.env` 中的默认密码
2. 不要将 `.env` 提交到 Git
3. 限制 PostgreSQL 端口仅内网访问
4. 定期备份数据

```bash
# 生成强密码
openssl rand -base64 32
```

---

## 📝 迁移 SQLite 数据

```python
# scripts/migrate_sqlite_to_pg.py
import sqlite3
import psycopg2
import json

# SQLite 连接
sqlite_conn = sqlite3.connect('data/qframe.db')
sqlite_conn.row_factory = sqlite3.Row

# PostgreSQL 连接
pg_conn = psycopg2.connect(
    "postgresql://quant:quant_password_2024@localhost:5432/qframe"
)
pg_cursor = pg_conn.cursor()

# 迁移 experiments
sqlite_cursor = sqlite_conn.cursor()
sqlite_cursor.execute("SELECT * FROM experiments")
for row in sqlite_cursor.fetchall():
    pg_cursor.execute("""
        INSERT INTO experiments (id, name, strategy, status, config, metrics, tags, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row['id'], row['name'], row['strategy'], row['status'],
        row['config'], row['metrics'],
        json.loads(row['tags']) if row['tags'] else None,
        row['created_at'], row['updated_at']
    ))

pg_conn.commit()
print("迁移完成！")
```

---

## 🆘 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker compose logs postgres

# 检查端口占用
sudo lsof -i :5432
```

### 连接被拒绝

```bash
# 检查防火墙
sudo ufw status

# 允许端口（如需远程访问）
sudo ufw allow 5432/tcp
```

### 性能问题

```sql
-- 查看慢查询
SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;

-- 查看连接数
SELECT count(*) FROM pg_stat_activity;

-- 查看表大小
SELECT 
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```
