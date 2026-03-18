# 量化训练系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vue 3](https://img.shields.io/badge/Vue-3.4-42b883)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)](https://fastapi.tiangolo.com/)
[![Naive UI](https://img.shields.io/badge/NaiveUI-2.38-18a058)](https://www.naiveui.com/)

A 股超短交易智能体训练框架 - 基于强化学习的量化交易系统

## ✨ 特性

- 🎯 **强化学习训练** - 支持 PPO、SAC、A2C 等算法
- 📊 **数据可视化** - ECharts 实时图表展示
- 🔄 **实时监控** - WebSocket 推送训练状态
- 🎨 **现代界面** - Naive UI 简约设计
- 📱 **响应式** - 支持桌面/平板/移动端
- 🔐 **用户认证** - JWT Token 安全认证

## 🚀 快速开始

### 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

## 📁 项目结构

```
.
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── services/    # 业务逻辑
│   │   ├── db/          # 数据库
│   │   └── schemas/     # 数据模型
│   ├── tests/           # 测试
│   └── requirements.txt
├── frontend/            # Vue 3 前端
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── components/ # 通用组件
│   │   ├── store/      # 状态管理
│   │   └── services/   # API 服务
│   └── package.json
├── docker/             # Docker 部署
└── docs/               # 文档
```

## 🎯 功能模块

| 模块 | 状态 | 说明 |
|------|------|------|
| 用户认证 | ✅ | JWT Token 认证 |
| 实验管理 | ✅ | CRUD 完整功能 |
| 模型管理 | ✅ | 模型注册/部署 |
| 训练任务 | ✅ | 任务队列/监控 |
| 数据管理 | ✅ | 股票数据下载 |
| 回测系统 | ⏳ | 开发中 |
| 实盘接口 | ⏳ | 规划中 |

## 📊 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端      │────▶│   后端      │────▶│   数据库    │
│  Vue 3      │◀────│  FastAPI    │◀────│  SQLite/PG  │
│  Naive UI   │     │  WebSocket  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 🔧 配置说明

### 环境变量

```bash
# .env
DATABASE_URL=sqlite:///data/qframe.db
TUSHARE_TOKEN=your_token_here
JWT_SECRET=your_secret_here
API_HOST=0.0.0.0
API_PORT=5000
```

### 数据库

- **开发环境：** SQLite（默认）
- **生产环境：** PostgreSQL（推荐）

## 📖 文档

- [功能评估报告](./功能评估报告.md)
- [功能完善报告](./功能完善报告.md)
- [前端开发文档](./frontend/README.md)
- [后端开发文档](./backend/README.md)
- [Docker 部署](./docker/README.md)

## 🛠️ 技术栈

**前端：**
- Vue 3.4 + TypeScript
- Naive UI 2.38
- Vue Router 4
- Pinia
- Axios
- ECharts 5.5

**后端：**
- FastAPI 0.104
- SQLAlchemy
- Pydantic
- Uvicorn
- Stable-Baselines3 (可选)
- PyTorch (可选)

## 📝 开发指南

### 添加新 API

1. 在 `backend/app/api/` 创建路由文件
2. 在 `backend/app/main.py` 注册
3. 在 `frontend/src/services/api.ts` 添加接口

### 添加新页面

1. 在 `frontend/src/views/` 创建组件
2. 在 `frontend/src/router.ts` 添加路由
3. 在 `frontend/src/layouts/MainLayout.vue` 添加菜单

## 🤝 贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

MIT License

## 📞 联系

- 项目地址：https://github.com/your-username/quant-trading-system
- 问题反馈：https://github.com/your-username/quant-trading-system/issues

---

**Made with ❤️ by Quant Team**
