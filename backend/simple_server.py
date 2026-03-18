"""简化版后端 - 用于前后端联调测试"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

app = FastAPI(title="Quant Trading API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟数据
mock_experiments = [
    {"id": "exp_001", "name": "动量策略 v1", "strategy": "Momentum", "status": "running", "config": {"steps": 10000}, "created_at": "2026-03-18T10:00:00"},
    {"id": "exp_002", "name": "反转策略 v2", "strategy": "Reversal", "status": "pending", "config": {"steps": 20000}, "created_at": "2026-03-18T09:30:00"},
    {"id": "exp_003", "name": "均值回归 v1", "strategy": "MeanReversion", "status": "completed", "config": {"steps": 15000}, "created_at": "2026-03-17T16:00:00"},
]

mock_models = [
    {"id": "model_001", "name": "PPO 最佳模型", "strategy": "PPO", "version": 3, "experiment_id": "exp_001", "metrics": {"reward": 0.85, "sharpe": 1.5}, "created_at": "2026-03-18T08:00:00"},
    {"id": "model_002", "name": "SAC 模型 v1", "strategy": "SAC", "version": 1, "experiment_id": "exp_002", "metrics": {"reward": 0.72}, "created_at": "2026-03-17T14:00:00"},
]

mock_tasks = [
    {"id": 1, "strategy": "PPO", "steps": 10000, "status": "running", "priority": 3, "created_at": "2026-03-18T10:30:00"},
    {"id": 2, "strategy": "SAC", "steps": 20000, "status": "pending", "priority": 5, "created_at": "2026-03-18T09:15:00"},
    {"id": 3, "strategy": "A2C", "steps": 15000, "status": "pending", "priority": 8, "created_at": "2026-03-18T08:45:00"},
]

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/agent/status")
async def get_status():
    return {
        "success": True,
        "message": "OK",
        "data": {
            "experiments": len(mock_experiments),
            "models": len(mock_models),
            "training_tasks": len(mock_tasks),
        }
    }

@app.get("/api/experiments")
async def list_experiments():
    return {"success": True, "message": "OK", "data": mock_experiments}

@app.post("/api/experiments")
async def create_experiment(data: dict):
    new_exp = {
        "id": f"exp_{len(mock_experiments) + 1:03d}",
        "name": data.get("name"),
        "strategy": data.get("strategy"),
        "status": "pending",
        "config": data.get("config", {}),
        "created_at": datetime.now().isoformat(),
    }
    mock_experiments.append(new_exp)
    return {"success": True, "message": "创建成功", "data": new_exp}

@app.get("/api/models")
async def list_models():
    return {"success": True, "message": "OK", "data": mock_models}

@app.post("/api/models")
async def register_model(data: dict):
    new_model = {
        "id": f"model_{len(mock_models) + 1:03d}",
        "name": data.get("name"),
        "strategy": data.get("strategy"),
        "version": 1,
        "experiment_id": data.get("experiment_id"),
        "metrics": data.get("metrics", {}),
        "model_path": data.get("model_path"),
        "created_at": datetime.now().isoformat(),
    }
    mock_models.append(new_model)
    return {"success": True, "message": "注册成功", "data": new_model}

@app.get("/api/queue")
async def get_queue():
    return {"success": True, "message": "OK", "data": mock_tasks}

@app.post("/api/train")
async def create_task(data: dict):
    new_task = {
        "id": len(mock_tasks) + 1,
        "strategy": data.get("strategy"),
        "steps": data.get("steps", 10000),
        "status": "pending",
        "priority": data.get("priority", 5),
        "created_at": datetime.now().isoformat(),
    }
    mock_tasks.append(new_task)
    return {"success": True, "message": "创建成功", "data": new_task}

@app.get("/api/auth/login")
async def login():
    return {"success": False, "message": "请使用 POST 方法"}

@app.post("/api/auth/login")
async def login_post(data: dict):
    return {
        "success": True,
        "message": "登录成功",
        "data": {
            "access_token": "mock_token_12345",
            "user": {
                "id": "user_001",
                "username": "admin",
                "email": "admin@example.com",
                "is_active": True,
                "is_superuser": True,
            }
        }
    }

if __name__ == "__main__":
    print("🚀 启动简化版后端服务...")
    print("📡 地址：http://localhost:5000")
    print("📖 文档：http://localhost:5000/docs")
    uvicorn.run(app, host="0.0.0.0", port=5000)
