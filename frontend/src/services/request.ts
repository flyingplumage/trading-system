import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import { message } from 'naive-ui'
import { h } from 'vue'
import type { VNode } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const request: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 401:
          message.error('未授权，请登录')
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          message.error('拒绝访问')
          break
        case 404:
          message.error('资源不存在')
          break
        case 500:
          message.error(data?.message || '服务器错误')
          break
        default:
          message.error(data?.message || '请求失败')
      }
    } else {
      message.error('网络错误')
    }
    return Promise.reject(error)
  }
)

export const apiRequest = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) =>
    request.get<any, { success: boolean; message: string; data: T }>(url, config),
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    request.post<any, { success: boolean; message: string; data: T }>(url, data, config),
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    request.put<any, { success: boolean; message: string; data: T }>(url, data, config),
  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    request.delete<any, { success: boolean; message: string; data: T }>(url, config),
}

export default request
