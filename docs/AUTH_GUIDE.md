# 认证授权指南

**更新时间:** 2026-03-16  
**版本:** v1.2.0

---

## 🔐 概述

系统现已实现完整的认证授权机制，支持：

- **JWT Token 认证** - 适用于前端、短期访问
- **API Key 认证** - 适用于智能体、长期访问
- **角色权限管理** - 4 种角色，细粒度权限控制

---

## 👥 用户角色

| 角色 | 说明 | 权限 |
|------|------|------|
| **admin** | 管理员 | 所有权限 |
| **developer** | 开发者 | 训练/回测/模型/数据读写 |
| **user** | 普通用户 | 只读权限 |
| **bot** | 机器人/智能体 | 训练/回测/数据 (OpenClaw 使用) |

---

## 🚀 快速开始

### 1. 创建管理员账户

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "role": "admin"
  }'
```

**响应:**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "user_id": "user_xxx",
    "username": "admin",
    "role": "admin"
  }
}
```

---

### 2. 登录获取 Token

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**响应:**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "user_id": "user_xxx",
    "username": "admin",
    "role": "admin",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
  }
}
```

---

### 3. 使用 Token 访问 API

```bash
# 获取当前用户信息
curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 启动训练任务
curl -X POST "http://localhost:5000/api/train/start?strategy=test&steps=1000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 🔑 API Key 管理 (智能体专用)

### 创建 API Key

```bash
# 先登录获取 Token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# 创建 API Key (给 OpenClaw 使用)
curl -X POST http://localhost:5000/api/auth/api-key/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenClaw-Lyra",
    "role": "bot",
    "expires_days": 365
  }'
```

**响应:**
```json
{
  "success": true,
  "message": "API Key 已创建",
  "data": {
    "api_key": "FDMxaWwvNoIsabnbcrZHy3oQ_GiFlgynt81rjTLKt4g",
    "name": "OpenClaw-Lyra",
    "role": "bot",
    "expires_days": 365
  }
}
```

⚠️ **注意:** API Key 只显示一次，请妥善保存！

---

### 使用 API Key 访问 API

```bash
# OpenClaw 智能体使用 API Key
curl -X POST "http://localhost:5000/api/train/start?strategy=momentum&steps=10000" \
  -H "X-API-Key: FDMxaWwvNoIsabnbcrZHy3oQ_GiFlgynt81rjTLKt4g"

# 查询训练任务
curl "http://localhost:5000/api/train/tasks" \
  -H "X-API-Key: FDMxaWwvNoIsabnbcrZHy3oQ_GiFlgynt81rjTLKt4g"

# 执行回测
curl -X POST "http://localhost:5000/api/agent/backtest/execute?model_id=xxx" \
  -H "X-API-Key: FDMxaWwvNoIsabnbcrZHy3oQ_GiFlgynt81rjTLKt4g"
```

---

### 列出 API Keys

```bash
curl http://localhost:5000/api/auth/api-key/list \
  -H "Authorization: Bearer $TOKEN"
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "key_prefix": "FDMxaWwv...",
      "name": "OpenClaw-Lyra",
      "username": "admin",
      "role": "bot",
      "created_at": "2026-03-16T16:02:00",
      "expires_at": "2027-03-16T16:02:00",
      "last_used": "2026-03-16T16:05:00",
      "usage_count": 15,
      "is_active": true
    }
  ]
}
```

---

### 撤销 API Key

```bash
curl -X POST http://localhost:5000/api/auth/api-key/revoke/FDMxaWwvNoIsabnbcrZHy3oQ_GiFlgynt81rjTLKt4g \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📋 权限矩阵

| 资源/操作 | create | read | update | delete | config |
|----------|--------|------|--------|--------|--------|
| **train** (训练) | admin, developer, bot | all | admin, developer | admin | - |
| **backtest** (回测) | admin, developer, bot | all | admin | admin | - |
| **model** (模型) | admin, developer | all | admin, developer | admin | - |
| **data** (数据) | admin, developer | all | admin, developer | admin | - |
| **queue** (队列) | admin, developer, bot | all | admin, developer | admin | admin, bot |
| **user** (用户) | admin | admin | admin | admin | - |

---

## 🔐 前端集成示例

### React + Axios

```javascript
// src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000',
});

// 请求拦截器 - 自动添加 Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - Token 过期自动刷新
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Token 过期，尝试刷新
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken
          });
          localStorage.setItem('access_token', res.data.data.access_token);
          // 重试原请求
          error.config.headers.Authorization = `Bearer ${res.data.data.access_token}`;
          return api(error.config);
        } catch {
          // 刷新失败，跳转登录
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

### 登录页面示例

```javascript
// src/pages/Login.js
import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Login() {
  const navigate = useNavigate();
  
  const handleLogin = async (values) => {
    try {
      const res = await axios.post('/api/auth/login', values);
      const { access_token, refresh_token } = res.data.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      message.success('登录成功');
      navigate('/');
    } catch (error) {
      message.error('登录失败：' + error.response?.data?.detail);
    }
  };
  
  return (
    <Form onFinish={handleLogin}>
      <Form.Item name="username" rules={[{ required: true }]}>
        <Input placeholder="用户名" />
      </Form.Item>
      <Form.Item name="password" rules={[{ required: true }]}>
        <Input.Password placeholder="密码" />
      </Form.Item>
      <Button type="primary" htmlType="submit">登录</Button>
    </Form>
  );
}
```

---

## 🤖 OpenClaw 智能体配置

### 环境变量方式

```bash
# .env 文件
TRADING_SYSTEM_API_KEY=FDMxaWwvNoIsabnbcrZHy3oQ_GiFlgynt81rjTLKt4g
TRADING_SYSTEM_API_URL=http://localhost:5000
```

### Python 调用示例

```python
# OpenClaw 智能体中使用
import os
import requests

API_KEY = os.getenv('TRADING_SYSTEM_API_KEY')
API_URL = os.getenv('TRADING_SYSTEM_API_URL')

headers = {'X-API-Key': API_KEY}

# 启动训练
response = requests.post(
    f'{API_URL}/api/train/start',
    headers=headers,
    params={'strategy': 'momentum', 'steps': 10000}
)

# 执行回测
response = requests.post(
    f'{API_URL}/api/agent/backtest/execute',
    headers=headers,
    params={'model_id': 'model_xxx'}
)
```

---

## 🛡️ 安全建议

### 生产环境配置

1. **使用强密码**
   ```bash
   # 密码至少 8 位，包含大小写+数字+符号
   ```

2. **启用 HTTPS**
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

3. **限制 API Key 权限**
   - 为不同服务创建不同 API Key
   - 设置合理的过期时间
   - 定期轮换密钥

4. **监控异常访问**
   ```bash
   # 查看 API Key 使用记录
   curl http://localhost:5000/api/auth/api-key/list \
     -H "Authorization: Bearer $TOKEN"
   ```

---

## 📝 API 参考

### 认证相关

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/auth/register` | POST | 用户注册 | ❌ |
| `/api/auth/login` | POST | 用户登录 | ❌ |
| `/api/auth/refresh` | POST | 刷新 Token | ❌ |
| `/api/auth/me` | GET | 当前用户 | ✅ |
| `/api/auth/users` | GET | 用户列表 | ✅ admin |
| `/api/auth/permissions` | GET | 权限查询 | ✅ |

### API Key 管理

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/auth/api-key/create` | POST | 创建 Key | ✅ |
| `/api/auth/api-key/list` | GET | 列出 Keys | ✅ |
| `/api/auth/api-key/revoke/{key}` | POST | 撤销 Key | ✅ |

---

## 🐛 常见问题

### Q: Token 过期了怎么办？

A: 使用 refresh token 刷新：
```bash
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

### Q: API Key 泄露了怎么办？

A: 立即撤销：
```bash
curl -X POST http://localhost:5000/api/auth/api-key/revoke/{key} \
  -H "Authorization: Bearer $TOKEN"
```

### Q: 如何为团队成员创建账户？

A: 管理员创建：
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"dev1","password":"xxx","role":"developer"}'
```

---

**Lyra 备注:** 认证系统已完整实现，建议生产环境启用 HTTPS 并定期轮换密钥。
