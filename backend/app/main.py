"""Iris Backend - Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

# 导入 WebSocket 路由
from app.api.websocket import router as websocket_router

app = FastAPI(title="Iris Backend", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 WebSocket 路由
app.include_router(websocket_router)

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
        "version": "v29",
        "worker_url": "/files/worker.py"
    }

@app.get("/deploy-mac-final.sh")
async def get_deploy_script():
    script_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/deploy-mac-final.sh"
    if os.path.exists(script_path):
        return FileResponse(script_path, media_type="text/x-shellscript", filename="deploy-mac-final.sh")
    return {"error": "Deploy script not found"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Iris Backend API"}

@app.get("/files/worker.py")
async def get_worker_file():
    """提供 Worker 代码下载"""
    worker_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/worker.py"
    if os.path.exists(worker_path):
        return FileResponse(worker_path, media_type="text/x-python", filename="worker.py")
    return {"error": "Worker file not found"}

@app.get("/files/deploy-mac-final.sh")
async def get_deploy_script_final():
    """提供最新部署脚本"""
    script_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/deploy-mac-final.sh"
    if os.path.exists(script_path):
        return FileResponse(script_path, media_type="text/x-shellscript", filename="deploy-mac-final.sh")
    return {"error": "Deploy script not found"}

@app.get("/files/deploy-mac-v2.sh")
async def get_deploy_script_v2():
    """提供 v2 部署脚本"""
    script_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/deploy-mac-v2.sh"
    if os.path.exists(script_path):
        return FileResponse(script_path, media_type="text/x-shellscript", filename="deploy-mac-v2.sh")
    return {"error": "Deploy script not found"}

@app.get("/files/deploy-mac-v3.sh")
async def get_deploy_script_v3():
    script_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/deploy-mac-v3.sh"
    if os.path.exists(script_path):
        return FileResponse(script_path, media_type="text/x-shellscript", filename="deploy-mac-v3.sh")
    return {"error": "Deploy script not found"}

@app.get("/files/deploy-mac-final.sh")
async def get_deploy_mac_final():
    script_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/deploy-mac-final.sh"
    if os.path.exists(script_path):
        return FileResponse(script_path, media_type="text/x-shellscript", filename="deploy-mac-final.sh")
    return {"error": "Deploy script not found"}

@app.get("/files/worker.py")
async def get_worker_py():
    """提供最新 Worker 代码"""
    worker_path = "/root/.openclaw/workspace/projects/trading-system-release/worker/worker.py"
    if os.path.exists(worker_path):
        return FileResponse(worker_path, media_type="text/x-python", filename="worker.py")
    return {"error": "Worker file not found"}
