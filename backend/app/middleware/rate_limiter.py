"""API 速率限制中间件 - 防止滥用"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time

class RateLimiter(BaseHTTPMiddleware):
    """简单的基于 IP 的速率限制"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端 IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 跳过静态文件和健康检查
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # 清理过期记录 (1 分钟前)
        current_time = time.time()
        self.request_history[client_ip] = [
            t for t in self.request_history[client_ip]
            if current_time - t < 60
        ]
        
        # 检查速率限制
        if len(self.request_history[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"速率限制：{self.requests_per_minute} 请求/分钟",
                    "retry_after": 60
                }
            )
        
        # 记录请求
        self.request_history[client_ip].append(current_time)
        
        # 继续处理请求
        return await call_next(request)


# 装饰器方式的路由级速率限制
def rate_limit(requests_per_minute: int = 30):
    """路由级别的速率限制装饰器"""
    from functools import wraps
    import time
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()
            
            # 简单的内存存储（生产环境建议用 Redis）
            if not hasattr(wrapper, 'history'):
                wrapper.history = defaultdict(list)
            
            # 清理过期记录
            wrapper.history[client_ip] = [
                t for t in wrapper.history[client_ip]
                if current_time - t < 60
            ]
            
            # 检查限制
            if len(wrapper.history[client_ip]) >= requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"速率限制：{requests_per_minute} 请求/分钟"
                )
            
            wrapper.history[client_ip].append(current_time)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
