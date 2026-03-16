/**
 * 统一错误处理工具
 */

import { message } from 'antd';

/**
 * HTTP 错误码映射
 */
const errorMessages = {
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '无权访问此资源',
  404: '请求的资源不存在',
  408: '请求超时',
  409: '资源冲突',
  422: '数据验证失败',
  429: '请求过于频繁，请稍后再试',
  500: '服务器错误，请稍后再试',
  502: '网关错误',
  503: '服务不可用',
  504: '网关超时'
};

/**
 * 处理 HTTP 错误
 * @param {Error} error - 错误对象
 * @param {Object} options - 配置选项
 */
export function handleHttpError(error, options = {}) {
  const {
    showMessage = true,
    onError,
    customMessages = {}
  } = options;

  let errorMessage = '操作失败';

  // Axios 错误
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;
    
    // 使用自定义消息或默认映射
    errorMessage = customMessages[status] || 
                   data?.detail || 
                   data?.message || 
                   errorMessages[status] || 
                   `错误 ${status}`;

    // 特殊处理 401
    if (status === 401) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
  } 
  // 网络错误
  else if (error.request) {
    errorMessage = '网络连接失败，请检查网络或服务器状态';
  }
  // 其他错误
  else {
    errorMessage = error.message || errorMessage;
  }

  // 显示错误消息
  if (showMessage) {
    message.error(errorMessage, 3);
  }

  // 回调
  onError?.(error, errorMessage);

  // 控制台输出
  console.error('[API Error]', error);

  return errorMessage;
}

/**
 * 创建错误处理装饰器
 * @param {Function} fn - 异步函数
 * @param {Object} options - 配置选项
 */
export function withErrorHandling(fn, options = {}) {
  return async function(...args) {
    try {
      return await fn(...args);
    } catch (error) {
      return handleHttpError(error, options);
    }
  };
}

/**
 * 验证响应数据
 * @param {Object} response - API 响应
 * @returns {boolean} 是否成功
 */
export function validateResponse(response) {
  if (!response) {
    console.error('[Validation] 响应为空');
    return false;
  }

  if (response.success === false) {
    console.error('[Validation]', response.message || '操作失败');
    return false;
  }

  return true;
}

export default {
  handleHttpError,
  withErrorHandling,
  validateResponse,
  errorMessages
};
