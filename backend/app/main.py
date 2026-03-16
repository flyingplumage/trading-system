"""Quantitative Trading System Backend"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import experiments, models, train, data, strategy, resources, health, scheduler, tushare, environments, queue, websocket, auth, model_export, analysis, sector_analysis, validation, optimization, explanation, worker, hardware
from app.api.agent import training_router, backtest_router, optimization_router, strategy_router
from app.schemas.schemas import Response
from app.services.websocket_manager import broadcaster

# 创建 FastAPI 应用
app = FastAPI(
    title="Quantitative Trading System API",
    description="A 股超短交易智能体训练框架",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# 启动 WebSocket 广播器
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    broadcaster.start()
    print("[System] WebSocket 广播器已启动")

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
