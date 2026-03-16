/**
 * API 服务配置（统一错误处理）
 */

import axios from 'axios';
import { message } from 'antd';
import { handleHttpError } from '../utils/errorHandler';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加 Token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 添加请求时间戳（防止缓存）
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      };
    }

    return config;
  },
  (error) => {
    console.error('[Request Error]', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 直接返回 data
    return response.data;
  },
  (error) => {
    // 统一错误处理
    handleHttpError(error, {
      showMessage: true,
      onError: (err, msg) => {
        console.error('[API Error]', msg);
      }
    });
    return Promise.reject(error);
  }
);

// 实验管理
export const experiments = {
  list: (status = null, limit = 100) => 
    api.get('/api/experiments', { params: { status, limit } }),
  
  get: (id) => 
    api.get(`/api/experiments/${id}`),
  
  create: (data) => 
    api.post('/api/experiments', data),
  
  update: (id, data) => 
    api.put(`/api/experiments/${id}`, data),
  
  delete: (id) => 
    api.delete(`/api/experiments/${id}`),
};

// 模型管理
export const models = {
  list: (strategy = null, limit = 100) => 
    api.get('/api/models', { params: { strategy, limit } }),
  
  best: (limit = 10) => 
    api.get('/api/models/best', { params: { limit } }),
  
  get: (id) => 
    api.get(`/api/models/${id}`),
  
  register: (data) => 
    api.post('/api/models/register', data),
};

// 训练管理
export const training = {
  start: (strategy, steps = 10000, priority = 5, useQueue = true, envName = 'momentum', stockCode = '000001.SZ') => 
    api.post('/api/train/start', null, { 
      params: { strategy, steps, priority, use_queue: useQueue, env_name: envName, stock_code: stockCode } 
    }),
  
  status: (taskId) => 
    api.get(`/api/train/status/${taskId}`),
  
  tasks: (status = null, limit = 100) => 
    api.get('/api/train/tasks', { params: { status, limit } }),
};

// 任务队列
export const queue = {
  enqueue: (strategy, steps = 10000, priority = 'normal', envName = 'momentum', stockCode = '000001.SZ') =>
    api.post('/api/queue/enqueue', null, {
      params: { strategy, steps, priority, env_name: envName, stock_code: stockCode }
    }),
  
  status: () =>
    api.get('/api/queue/status'),
  
  position: (taskId) =>
    api.get(`/api/queue/position/${taskId}`),
  
  cancel: (taskId) =>
    api.post(`/api/queue/cancel/${taskId}`),
  
  config: (maxConcurrent = 1) =>
    api.post('/api/queue/config', null, { params: { max_concurrent: maxConcurrent } }),
  
  tasks: (status = null) =>
    api.get('/api/queue/tasks', { params: { status } }),
};

// 回测管理
export const backtest = {
  execute: (modelId, stockCode = '000001.SZ', envName = 'momentum', initialCash = 1000000) =>
    api.post('/api/agent/backtest/execute', null, {
      params: { model_id: modelId, stock_code: stockCode, env_name: envName, initial_cash: initialCash }
    }),
  
  task: (taskId) =>
    api.get(`/api/agent/backtest/task/${taskId}`),
  
  evaluate: (modelId, stockCodes = ['000001.SZ'], envNames = ['momentum']) =>
    api.post('/api/agent/backtest/evaluate', null, {
      params: { model_id: modelId, stock_codes: stockCodes, env_names: envNames }
    }),
  
  modelSummary: (modelId) =>
    api.get(`/api/agent/backtest/models/${modelId}/summary`),
  
  compare: (experimentIds) =>
    api.post('/api/agent/backtest/compare', experimentIds),
};

// WebSocket
export const ws = {
  url: process.env.REACT_APP_WS_URL || 'ws://localhost:5000/ws',
  
  getInfo: () =>
    api.get('/ws/info'),
};

// 数据服务
export const data = {
  stocks: () => 
    api.get('/api/data/stocks'),
  
  price: (code, limit = 1000) => 
    api.get(`/api/data/price/${code}`, { params: { limit } }),
  
  features: (code, limit = 1000) => 
    api.get(`/api/data/features/${code}`, { params: { limit } }),
  
  stats: () => 
    api.get('/api/data/stats'),
};

// 调度器
export const scheduler = {
  status: () => 
    api.get('/api/scheduler/status'),
  
  config: (params) => 
    api.get('/api/scheduler/config', { params }),
  
  queueStatus: () => 
    api.get('/api/scheduler/queue/status'),
  
  queueTasks: (params) => 
    api.get('/api/scheduler/queue/tasks', { params }),
  
  cancelTask: (taskId) => 
    api.post(`/api/scheduler/queue/task/${taskId}/cancel`),
};

// OpenClaw 智能体
export const agent = {
  status: () => 
    api.get('/api/agent/status'),
  
  train: (strategy, steps = 100000) => 
    api.post('/api/agent/train', null, { params: { strategy, steps } }),
};

// 健康检查
export const health = () => 
  api.get('/health');

// 认证管理
export const auth = {
  register: (data) => 
    api.post('/api/auth/register', data),
  
  login: (credentials) => 
    api.post('/api/auth/login', credentials),
  
  refresh: (refreshToken) => 
    api.post('/api/auth/refresh', { refresh_token: refreshToken }),
  
  me: () => 
    api.get('/api/auth/me'),
  
  users: () => 
    api.get('/api/auth/users'),
  
  createUser: (data) => 
    api.post('/api/auth/register', data),
  
  updateUser: (username, data) => 
    api.put(`/api/auth/users/${username}`, data),
  
  deleteUser: (username) => 
    api.delete(`/api/auth/users/${username}`),
  
  permissions: () => 
    api.get('/api/auth/permissions'),
  
  // API Key
  createApiKey: (data) => 
    api.post('/api/auth/api-key/create', data),
  
  listApiKeys: () => 
    api.get('/api/auth/api-key/list'),
  
  revokeApiKey: (key) => 
    api.post(`/api/auth/api-key/revoke/${encodeURIComponent(key)}`),
};

export default api;
