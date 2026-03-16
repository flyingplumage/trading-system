# 前端部署指南

**更新时间:** 2026-03-16  
**版本:** v1.1.0

---

## 📱 页面列表

| 页面 | 路由 | 功能说明 |
|------|------|----------|
| Dashboard | `/` | 系统概览、统计指标 |
| 训练监控 | `/training` | 训练任务列表、实时进度、WebSocket 推送 |
| 回测管理 | `/backtest` | 执行回测、批量评估、结果展示 |
| 任务队列 | `/queue` | 队列状态、任务调度、并发配置 |
| 实验管理 | `/experiments` | 实验列表、详情 |
| 模型管理 | `/models` | 模型列表、最佳模型 |
| OpenClaw | `/agent` | 智能体状态 |
| 资源监控 | `/resources` | 系统资源、GPU 状态 |
| 调度器 | `/scheduler` | 定时任务管理 |

---

## 🚀 开发环境启动

### 前置条件

- Node.js >= 16
- npm >= 8
- 后端服务运行在 `http://localhost:5000`

### 启动步骤

```bash
# 进入前端目录
cd frontend

# 安装依赖 (首次)
npm install

# 启动开发服务器
npm run start

# 访问 http://localhost:3000
```

### 环境变量

创建 `.env` 文件 (可选):

```bash
# 后端 API 地址
REACT_APP_API_URL=http://localhost:5000

# WebSocket 地址
REACT_APP_WS_URL=ws://localhost:5000/ws
```

---

## 📦 生产环境构建

```bash
# 构建生产版本
npm run build

# 构建并分析包大小
npm run build:analyze

# 输出目录：build/
```

### 部署到 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/build;
    index index.html;
    
    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 反向代理
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket 代理
    location /ws {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 🎨 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| React | 18.2.0 | UI 框架 |
| Ant Design | 5.12.0 | UI 组件库 |
| React Router | 6.20.0 | 路由管理 |
| Axios | 1.6.0 | HTTP 客户端 |
| Recharts | 2.10.0 | 图表库 |
| @ant-design/charts | 2.6.7 | 业务图表 |

---

## 📁 目录结构

```
frontend/
├── src/
│   ├── pages/              # 页面组件
│   │   ├── Dashboard.js    # 首页
│   │   ├── Training.js     # 训练监控
│   │   ├── Backtest.js     # 回测管理 (新增)
│   │   ├── Queue.js        # 任务队列 (新增)
│   │   ├── Experiments.js
│   │   ├── Models.js
│   │   ├── Agent.js
│   │   ├── Resources.js
│   │   ├── Scheduler.js
│   │   └── StrategyUpload.js
│   ├── components/         # 可复用组件
│   ├── services/           # API 服务
│   │   └── api.js          # 统一 API 封装
│   ├── utils/              # 工具函数
│   ├── App.js              # 主应用
│   └── index.js            # 入口
├── public/                 # 静态资源
├── package.json
└── webpack.config.js
```

---

## 🔌 API 调用示例

### 启动训练任务

```javascript
import { training } from '@/services/api';

// 使用队列
await training.start('momentum_v1', 10000, 5, true);

// 直接执行
await training.start('momentum_v1', 10000, 5, false);
```

### 执行回测

```javascript
import { backtest } from '@/services/api';

// 单个回测
const result = await backtest.execute(
  'model_xxx',
  '000001.SZ',
  'momentum',
  1000000
);

// 批量评估
const evaluation = await backtest.evaluate(
  'model_xxx',
  ['000001.SZ', '000002.SZ'],
  ['momentum']
);
```

### WebSocket 连接

```javascript
const ws = new WebSocket('ws://localhost:5000/ws?topics=training');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'training_progress') {
    console.log(`进度：${data.progress}%`);
  }
};
```

---

## 🐛 常见问题

### 1. 跨域问题

**症状:** 浏览器控制台显示 CORS 错误

**解决:** 确保后端 CORS 配置正确：

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. WebSocket 连接失败

**症状:** WebSocket 无法连接

**检查:**
1. 后端服务是否运行
2. 防火墙是否开放 5000 端口
3. Nginx 是否正确配置 WebSocket 代理

### 3. 构建失败

**症状:** `npm run build` 报错

**尝试:**
```bash
# 清理 node_modules
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📊 性能优化

### 代码分割

已实现路由级别的懒加载：

```javascript
const Training = lazy(() => import('./pages/Training'));
```

### 组件优化

- 使用 `React.memo` 避免不必要的重渲染
- 使用 `useMemo` 缓存计算结果
- 使用 `useCallback` 缓存函数引用

---

## 🎯 下一步

- [ ] 添加图表可视化 (资金曲线、收益对比)
- [ ] 实现深色模式
- [ ] 添加国际化支持
- [ ] 优化移动端适配
- [ ] 添加 PWA 支持

---

**Lyra 备注:** 前端核心功能已实现，与后端 API 完全对接。可以根据实际需求继续扩展可视化功能。
