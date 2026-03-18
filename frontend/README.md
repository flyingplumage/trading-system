# 量化训练系统前端 - Naive UI 版

基于 **Vue 3 + Naive UI** 的现代化管理后台界面

## 🎨 技术栈

- **框架:** Vue 3.4
- **UI 库:** Naive UI 2.38
- **状态管理:** Pinia
- **路由:** Vue Router 4
- **HTTP:** Axios
- **图表:** ECharts
- **构建工具:** Vite 5

## 🚀 快速开始

### 安装 Node.js

如未安装 Node.js：

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node -v && npm -v
```

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
# 配置环境变量（已默认配置）
cp .env.example .env 2>/dev/null || true

# 启动
npm run dev

# 访问 http://localhost:3000
```

### 默认账号

```
用户名：admin
密码：admin123
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── layouts/          # 布局组件
│   │   └── MainLayout.vue
│   ├── views/            # 页面组件
│   │   ├── Login.vue
│   │   ├── Dashboard.vue
│   │   ├── Experiments.vue
│   │   └── ...
│   ├── store/            # 状态管理
│   │   ├── auth.ts
│   │   ├── theme.ts
│   │   └── system.ts
│   ├── services/         # API 服务
│   │   ├── request.ts
│   │   └── api.ts
│   ├── types/            # TypeScript 类型
│   ├── styles/           # 样式文件
│   ├── App.vue
│   ├── main.ts
│   └── router.ts
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 🎯 已实现功能

### ✅ 已完成

- [x] 登录页面（渐变背景 + 表单验证）
- [x] 主布局（侧边栏 + 顶栏）
- [x] 仪表盘（统计卡片 + 任务队列）
- [x] 实验管理（CRUD 操作）
- [x] 主题切换（明/暗模式）
- [x] 响应式设计
- [x] API 请求封装

### ⏳ 开发中

- [ ] 模型管理
- [ ] 训练任务监控
- [ ] 数据管理
- [ ] WebSocket 实时推送
- [ ] 图表可视化

## 🎨 设计特点

### Naive UI 风格

- **简洁现代** - 清爽配色、圆角设计
- **组件丰富** - 50+ 高质量组件
- **TypeScript** - 完整类型支持
- **主题定制** - 支持明暗主题切换

### 配色方案

```
主色：#1677ff (科技蓝)
成功：#52c41a
警告：#faad14
错误：#ff4d4f
背景：#f5f7fa (浅灰)
```

## 📊 页面对比

| 页面 | 状态 | 说明 |
|------|------|------|
| 登录页 | ✅ | 渐变背景 + 表单验证 |
| 仪表盘 | ✅ | 4 个统计卡片 + 任务列表 |
| 实验管理 | ✅ | 表格 + 弹窗 CRUD |
| 模型管理 | ⏳ | 占位页面 |
| 训练任务 | ⏳ | 占位页面 |
| 数据管理 | ⏳ | 占位页面 |

## 🔧 开发命令

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 类型检查
npm run type-check
```

## 🌐 在线参考

**Naive UI 官方文档：** https://www.naiveui.com/

**类似项目：**
- Naive UI Admin: https://jekip.github.io/naive-admin/
- Naive UI Pro: https://pro.naiveui.com/

## 📦 部署

### Docker 部署

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## ⚠️ 注意事项

1. **生产环境修改默认密码**
2. **配置正确的 API 地址**（.env 文件）
3. **后端需启用 CORS**
4. **建议使用 HTTPS**

## 📄 许可证

MIT License
