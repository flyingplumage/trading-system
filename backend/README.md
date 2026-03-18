# 量化训练系统后端

A 股超短交易智能体训练框架 - FastAPI 后端服务

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4
```

### 访问服务

- **API 文档**: http://localhost:5000/docs
- **备用文档**: http://localhost:5000/redoc
- **健康检查**: http://localhost:5000/health

---

## 📁 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由层
│   │   ├── auth.py       # 认证相关
│   │   ├── experiments.py # 实验管理
│   │   ├── models.py     # 模型管理
│   │   ├── train.py      # 训练管理
│   │   └── ...
│   ├── services/         # 业务逻辑层
│   │   ├── trainer.py    # 训练服务
│   │   ├── backtest.py   # 回测服务
│   │   └── tushare_service.py # 数据服务
│   ├── db/               # 数据库层
│   │   ├── database.py   # 数据库操作
│   │   └── connection_pool.py # 连接池
│   ├── schemas/          # Pydantic 模型
│   └── main.py           # 应用入口
├── tests/                # 测试目录
├── configs/              # 配置文件
├── data/                 # 数据目录
├── shared/               # 共享资源
└── requirements.txt      # 依赖列表
```

---

## 🧪 运行测试

```bash
# 安装测试依赖
pip install -r tests/requirements-test.txt

# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行单个测试文件
pytest tests/test_database.py -v
```

---

## 📡 API 端点

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/api-key/create` - 创建 API Key

### 实验管理
- `GET /api/experiments` - 获取实验列表
- `POST /api/experiments` - 创建实验
- `GET /api/experiments/{id}` - 获取实验详情
- `PUT /api/experiments/{id}` - 更新实验

### 模型管理
- `GET /api/models` - 获取模型列表
- `POST /api/models` - 注册模型
- `GET /api/models/best` - 获取最佳模型

### 训练管理
- `POST /api/train` - 创建训练任务
- `GET /api/queue` - 获取任务队列
- `GET /api/agent/status` - 获取 Agent 状态

### 数据服务
- `GET /api/data/stocks` - 获取股票列表
- `GET /api/data/daily` - 获取日线数据
- `POST /api/data/update` - 更新数据

---

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 URL | `sqlite:///data/qframe.db` |
| `TUSHARE_TOKEN` | Tushare API Token | - |
| `JWT_SECRET` | JWT 加密密钥 | - |
| `API_HOST` | 服务监听地址 | `0.0.0.0` |
| `API_PORT` | 服务端口 | `5000` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

---

## 📊 数据库

### SQLite（开发环境）

```bash
# 自动初始化，无需额外配置
# 数据存储在 data/qframe.db
```

### PostgreSQL（生产环境）

```bash
# 使用 Docker 启动
cd docker
docker compose up -d

# 修改 .env
DATABASE_URL=postgresql://quant:password@localhost:5432/qframe
```

---

## 🔐 安全建议

1. **生产环境修改默认密码**
2. **不要提交 `.env` 到 Git**
3. **限制 CORS 白名单**
4. **使用 HTTPS**

---

## 📝 开发指南

### 添加新 API

1. 在 `app/api/` 创建新路由文件
2. 在 `app/main.py` 注册路由
3. 在 `app/schemas/` 定义数据模型
4. 编写测试用例

### 添加新服务

1. 在 `app/services/` 创建服务类
2. 继承 `ServiceBase` 基类
3. 实现 CRUD 方法

---

## 🆘 故障排查

### 常见问题

**数据库锁定**
```bash
# SQLite WAL 模式已启用，如仍锁定请检查：
sqlite3 data/qframe.db "PRAGMA journal_mode;"
# 应返回：wal
```

**端口被占用**
```bash
# 查找占用端口的进程
lsof -i :5000
# 杀死进程
kill -9 <PID>
```

**依赖冲突**
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📄 许可证

MIT License
