"""Iris Backend - Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

# 导入 WebSocket 路由
from app.api.websocket import router as websocket_router

# 导入智能体编排路由
from app.api.agent import training_router, backtest_router, optimization_router, strategy_router

# 导入速率限制中间件
from app.middleware.rate_limiter import RateLimiter

# 导入分析 API 路由
from app.api.analytics import router as analytics_router

app = FastAPI(title="Iris Backend", version="2.1")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 速率限制 (60 请求/分钟)
app.add_middleware(RateLimiter, requests_per_minute=60)

# 注册 WebSocket 路由
app.include_router(websocket_router)

# 注册智能体编排路由 (各模块已有自己的 prefix)
app.include_router(training_router)
app.include_router(backtest_router)
app.include_router(optimization_router)
app.include_router(strategy_router)

# 注册分析 API 路由
app.include_router(analytics_router)

# 打印路由信息
print("📋 已注册路由:")
print("  - WebSocket: /ws/*")
print("  - 训练监控：/api/agent/training/*")
print("  - 回测：/backtest/*")
print("  - 优化：/api/agent/optimization/*")
print("  - 策略：/api/agent/strategy/*")
print("  - 分析查询：/api/analytics/*")

# HTTP 文件服务
@app.get("/files/worker.py")
async def get_worker_code():
    worker_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/worker.py"
    if os.path.exists(worker_path):
        return FileResponse(worker_path, media_type="text/x-python", filename="worker.py")
    return {"error": "Worker code not found"}

@app.get("/files/deploy-mac-v31.sh")
async def get_deploy_script():
    script_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/deploy-mac-v31.sh"
    if os.path.exists(script_path):
        return FileResponse(script_path, media_type="text/x-shellscript", filename="deploy-mac-v31.sh")
    return {"error": "Deploy script not found"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/files/version")
async def get_version():
    return {
        "version": "v31",
        "worker_url": "/files/worker.py"
    }

@app.get("/")
async def root():
    return {"message": "Iris Backend API v2.0 - Optimized"}
