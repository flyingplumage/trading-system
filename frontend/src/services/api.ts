import { apiRequest } from './request'
import type { Experiment, Model, TrainingTask, SystemStats, LoginParams, UserInfo } from '@/types'

export const authApi = {
  login: (data: LoginParams) =>
    apiRequest.post<{ access_token: string; user: UserInfo }>('/api/auth/login', data),
  register: (data: { username: string; password: string; email?: string }) =>
    apiRequest.post('/api/auth/register', data),
}

export const experimentApi = {
  list: (params?: { status?: string; limit?: number }) =>
    apiRequest.get<Experiment[]>('/api/experiments', { params }),
  get: (id: string) =>
    apiRequest.get<Experiment>(`/api/experiments/${id}`),
  create: (data: { name: string; strategy: string; config?: Record<string, any> }) =>
    apiRequest.post<Experiment>('/api/experiments', data),
  update: (id: string, data: Partial<Experiment>) =>
    apiRequest.put<Experiment>(`/api/experiments/${id}`, data),
  delete: (id: string) =>
    apiRequest.delete(`/api/experiments/${id}`),
}

export const modelApi = {
  list: (params?: { strategy?: string; limit?: number }) =>
    apiRequest.get<Model[]>('/api/models', { params }),
  getBest: (limit?: number) =>
    apiRequest.get<Model[]>(`/api/models/best?limit=${limit || 10}`),
  register: (data: { name: string; strategy: string; experiment_id: string; metrics: Record<string, any>; model_path: string }) =>
    apiRequest.post<Model>('/api/models', data),
}

export const trainingApi = {
  create: (data: { strategy: string; steps: number; priority?: number }) =>
    apiRequest.post<TrainingTask>('/api/train', data),
  getQueue: () =>
    apiRequest.get<TrainingTask[]>('/api/queue'),
  getTask: (id: number) =>
    apiRequest.get<TrainingTask>(`/api/train/${id}`),
}

export const systemApi = {
  health: () =>
    apiRequest.get('/health'),
  getStatus: () =>
    apiRequest.get<SystemStats>('/api/agent/status'),
}
