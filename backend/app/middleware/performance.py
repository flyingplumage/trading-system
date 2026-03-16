"""
性能监控中间件
- 请求响应时间追踪
- 慢查询日志
- 性能统计
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("performance")


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, slow_threshold: float = 1.0):
        """
        初始化中间件
        
        Args:
            slow_threshold: 慢请求阈值（秒）
        """
        super().__init__(app)
        self.slow_threshold = slow_threshold
        self.stats = {
            'total_requests': 0,
            'total_time': 0,
            'slow_requests': 0,
            'by_endpoint': {}
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()
        
        # 执行请求
        response = await call_next(request)
        
        # 计算耗时
        process_time = time.time() - start_time
        process_time_ms = process_time * 1000
        
        # 更新统计
        self.stats['total_requests'] += 1
        self.stats['total_time'] += process_time
        
        # 记录端点统计
        endpoint = f"{request.method} {request.url.path}"
        if endpoint not in self.stats['by_endpoint']:
            self.stats['by_endpoint'][endpoint] = {
                'count': 0,
                'total_time': 0,
                'max_time': 0
            }
        
        ep_stats = self.stats['by_endpoint'][endpoint]
        ep_stats['count'] += 1
        ep_stats['total_time'] += process_time
        ep_stats['max_time'] = max(ep_stats['max_time'], process_time)
        
        # 记录慢请求
        if process_time > self.slow_threshold:
            self.stats['slow_requests'] += 1
            logger.warning(
                f"慢请求：{endpoint}",
                extra={
                    'process_time_ms': process_time_ms,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code
                }
            )
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time_ms)
        
        return response
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 计算平均值
        if stats['total_requests'] > 0:
            stats['avg_time_ms'] = (stats['total_time'] / stats['total_requests']) * 1000
        else:
            stats['avg_time_ms'] = 0
        
        # 计算端点平均时间
        for endpoint, ep_stats in stats['by_endpoint'].items():
            if ep_stats['count'] > 0:
                ep_stats['avg_time_ms'] = (ep_stats['total_time'] / ep_stats['count']) * 1000
            else:
                ep_stats['avg_time_ms'] = 0
        
        return stats


class CacheControlMiddleware(BaseHTTPMiddleware):
    """缓存控制中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 静态资源缓存 1 年
        if request.url.path.startswith('/static/'):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        
        # API 响应不缓存
        elif request.url.path.startswith('/api/'):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response
