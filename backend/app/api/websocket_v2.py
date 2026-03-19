"""WebSocket API v2 - 支持日志实时收集"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime

router = APIRouter()

# Worker 连接和日志
worker_connections: Dict[str, WebSocket] = {}
worker_logs: Dict[str, List[dict]] = {}
worker_status: Dict[str, dict] = {}

@router.websocket("/ws/worker")
async def worker_endpoint(websocket: WebSocket):
    """Worker WebSocket 端点"""
    worker_id = None
    try:
        await websocket.accept()
        message = await websocket.receive_json()
        if message.get("type") == "handshake":
            worker_id = message.get("worker_id", "unknown")
            worker_connections[worker_id] = websocket
            worker_logs[worker_id] = []
            worker_status[worker_id] = {
                "connected": True,
                "connected_at": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
            print(f"✅ Worker 已连接：{worker_id}")
            await websocket.send_json({"type": "ack", "message": "连接成功"})
            
            while True:
                try:
                    data = await websocket.receive_json()
                    msg_type = data.get("type", "")
                    worker_status[worker_id]["last_seen"] = datetime.now().isoformat()
                    
                    # 收集日志
                    if msg_type == "log":
                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "worker_id": worker_id,
                            "level": data.get("level", "info"),
                            "message": data.get("message", "")
                        }
                        worker_logs[worker_id].append(log_entry)
                        if len(worker_logs[worker_id]) > 500:
                            worker_logs[worker_id].pop(0)
                        print(f"[{worker_id}] {log_entry['level'].upper()}: {log_entry['message']}")
                    
                    # 收集状态
                    elif msg_type == "status":
                        worker_status[worker_id].update(data.get("data", {}))
                    
                except WebSocketDisconnect:
                    break
    except WebSocketDisconnect:
        print(f"❌ Worker 断开：{worker_id}")
    finally:
        if worker_id:
            if worker_id in worker_connections:
                del worker_connections[worker_id]
            if worker_id in worker_status:
                worker_status[worker_id]["connected"] = False
                worker_status[worker_id]["disconnected_at"] = datetime.now().isoformat()

@router.get("/ws/workers")
async def list_workers():
    """列出所有 Worker"""
    workers = []
    for wid, status in worker_status.items():
        workers.append({
            "worker_id": wid,
            "connected": status.get("connected", False),
            "connected_at": status.get("connected_at"),
            "last_seen": status.get("last_seen")
        })
    return {"workers": workers, "count": len(workers)}

@router.get("/ws/worker/{worker_id}/logs")
async def get_worker_logs(worker_id: str, limit: int = 50):
    """获取指定 Worker 的日志"""
    logs = worker_logs.get(worker_id, [])
    return {"worker_id": worker_id, "logs": logs[-limit:], "count": len(logs)}

@router.get("/ws/worker/{worker_id}/status")
async def get_worker_status(worker_id: str):
    """获取指定 Worker 的状态"""
    status = worker_status.get(worker_id, {})
    return status

@router.post("/ws/worker/command")
async def send_command(command: dict):
    """发送指令到 Worker"""
    worker_id = command.get("worker_id")
    msg_type = command.get("type")
    data = command.get("data", {})
    message = {"type": msg_type, "data": data}
    
    if worker_id and worker_id in worker_connections:
        try:
            await worker_connections[worker_id].send_json(message)
            return {"success": True, "message": f"指令已发送到 {worker_id}"}
        except:
            return {"success": False, "message": "发送失败"}
    else:
        # 广播到所有 Worker
        for wid in list(worker_connections.keys()):
            try:
                await worker_connections[wid].send_json(message)
            except:
                pass
        return {"success": True, "message": f"指令已广播到 {len(worker_connections)} 个 Worker"}
