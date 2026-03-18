export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
  error_code?: string
}

export interface UserInfo {
  id: string
  username: string
  email?: string
  is_active: boolean
  is_superuser: boolean
}

export interface LoginParams {
  username: string
  password: string
}

export interface Experiment {
  id: string
  name: string
  strategy: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  config: Record<string, any>
  metrics?: Record<string, any>
  tags?: string[]
  created_at: string
  updated_at?: string
}

export interface Model {
  id: string
  name: string
  strategy: string
  version: number
  experiment_id: string
  metrics: Record<string, any>
  model_path: string
  model_hash: string
  created_at: string
}

export interface TrainingTask {
  id: number
  strategy: string
  steps: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  priority: number
  experiment_id?: string
  result?: Record<string, any>
  error?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface SystemStats {
  experiments: number
  models: number
  training_tasks: number
}
