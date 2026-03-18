"""Quantitative Trading System Backend"""

import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import experiments, models, train, data, strategy, resources, health, scheduler, tushare, environments, queue, websocket, auth, model_export, analysis, sector_analysis, validation, optimization, explanation, worker, hardware
from app.api.agent import training_router, backtest_router, optimization_router, strategy_router
from app.schemas.schemas import Response
from app.services.websocket_manager import broadcaster

# 配置日志
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Quantitative Trading System API",
    description="A 股超短交易智能体训练框架",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 全局异常处理 ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    HTTP 异常处理（404, 405 等）
    """
    logger.warning(f"HTTP 异常：{exc.status_code} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "error_code": f"HTTP_{exc.status_code}"
        }
    )


@app.exception_handler(HTTPException)
async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
    """
    FastAPI HTTP 异常处理
    """
    logger.warning(f"HTTP 异常：{exc.status_code} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "error_code": f"HTTP_{exc.status_code}"
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求参数验证异常处理
    """
    logger.warning(f"参数验证失败：{exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "请求参数验证失败",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Pydantic 验证异常处理
    """
    logger.warning(f"Pydantic 验证失败：{exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "数据验证失败",
            "error_code": "PYDANTIC_VALIDATION_ERROR",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理（未捕获的异常）
    生产环境应隐藏详细错误信息
    """
    logger.error(f"未捕获异常：{type(exc).__name__} - {str(exc)}", exc_info=True)
    
    # 生产环境不返回详细错误信息
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error_code": "INTERNAL_ERROR"
        }
    )


# ==================== 请求日志中间件 ====================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    记录所有请求的日志
    """
    logger.info(f"请求：{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"响应：{request.method} {request.url.path} - {response.status_code}")
    return response


# 注册路由
app.include_router(auth.router)
app.include_router(experiments.router)
app.include_router(models.router)
app.include_router(train.router)
app.include_router(data.router)
app.include_router(strategy.router)
app.include_router(resources.router)
app.include_router(scheduler.router)
app.include_router(health.router)
app.include_router(tushare.router)
app.include_router(environments.router)
app.include_router(queue.router)
app.include_router(websocket.router)
app.include_router(model_export.router)
app.include_router(analysis.router)
app.include_router(sector_analysis.router)
app.include_router(validation.router)
app.include_router(optimization.router)
app.include_router(explanation.router)
app.include_router(worker.router)
app.include_router(hardware.router)

# 注册智能体 API
app.include_router(training_router, prefix='/api/agent', tags=['agent'])
app.include_router(backtest_router, prefix='/api/agent', tags=['agent'])
app.include_router(optimization_router, prefix='/api/agent', tags=['agent'])
app.include_router(strategy_router, prefix='/api/agent', tags=['agent'])

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# 智能体状态
@app.get("/api/agent/status")
async def agent_status():
    """获取智能体系统状态"""
    from app.db import get_db_stats
    stats = get_db_stats()
    return Response(
        success=True,
        message="OK",
        data={
            'status': 'running',
            'experiments': stats['experiments'],
            'models': stats['models'],
            'pending_tasks': stats['training_tasks'],
        }
    )

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    logger.info("[System] 应用启动中...")
    
    # 初始化数据库
    from app.db import database
    database.init_db()
    logger.info("[System] 数据库初始化完成")
    
    # 启动 WebSocket 广播器
    broadcaster.start()
    logger.info("[System] WebSocket 广播器已启动")
    
    logger.info("[System] 应用启动完成")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("[System] 应用关闭中...")
    
    # 停止 WebSocket 广播器
    try:
        broadcaster.stop()
        logger.info("[System] WebSocket 广播器已停止")
    except Exception as e:
        logger.error(f"[System] 停止广播器失败：{e}")
    
    logger.info("[System] 应用已关闭")

# 根路径
@app.get("/", response_model=Response)
async def root():
    return Response(
        success=True,
        message="Quantitative Trading System API v1.1.0",
        data={
            "docs": "/docs",
            "health": "/health",
            "auth": "/api/auth/login",
            "websocket": "/ws",
            "apis": [
                "/api/auth/register",
                "/api/auth/login",
                "/api/auth/api-key/create",
                "/api/train",
                "/api/queue",
                "/api/agent/backtest",
                "/api/models",
                "/api/experiments"
            ]
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
