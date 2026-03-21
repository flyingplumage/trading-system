"""WebSocket API - Worker 连接管理 + 任务管理 (支持逐个依赖安装)"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
import json
import asyncio
import time
from datetime import datetime
from app.services.task_manager import task_manager
from app.services.dependency_installer import dependency_installer

router = APIRouter()

@router.websocket("/ws/worker")
async def worker_endpoint(websocket: WebSocket):
    """Worker WebSocket 端点"""
    worker_id = None
    try:
        await websocket.accept()
        message = await websocket.receive_json()
        
        if message.get("type") == "handshake":
            worker_id = message.get("worker_id", "unknown")
            worker_version = message.get("version", "unknown")
            
            # 注册 Worker (带版本号)
            task_manager.register_worker(worker_id, websocket, worker_version)
            
            print(f"✅ Worker 已连接：{worker_id} (v{worker_version})")
            
            await websocket.send_json({
                "type": "ack",
                "message": "连接成功",
                "worker_id": worker_id,
                "server_tasks": task_manager.get_all_tasks()
            })
            
            # 发送所有任务（包括已完成的）
            all_tasks = task_manager.get_all_tasks()
            if all_tasks:
                await websocket.send_json({
                    "type": "active_tasks",
                    "tasks": all_tasks
                })
            
            while True:
                try:
                    data = await websocket.receive_json()
                    msg_type = data.get("type", "")
                    
                    # Worker 上报进度
                    if msg_type == "progress":
                        task_id = data.get("task_id")
                        progress = data.get("progress", 0)
                        status = data.get("status", "running")
                        extra = {k: v for k, v in data.items() if k not in ["type", "task_id", "progress", "status"]}
                        
                        if task_id:
                            # 更新任务进度
                            task_manager.update_worker_progress(worker_id, task_id, progress, status, extra)
                            print(f"📊 [{worker_id}] 任务 {task_id} 进度：{progress}%")
                    
                    # Worker 上报日志
                    elif msg_type == "log":
                        level = data.get("level", "info")
                        message_text = data.get("message", "")
                        print(f"[{worker_id}] [{level}] {message_text}")
                    
                    # Worker 完成任务
                    elif msg_type == "complete":
                        task_id = data.get("task_id")
                        result = data.get("result", {})
                        if task_id:
                            task_manager.complete_task(task_id, result)
                            print(f"✅ [{worker_id}] 任务完成：{task_id}")
                    
                    # Worker 报告错误
                    elif msg_type == "error":
                        task_id = data.get("task_id")
                        error = data.get("error", "")
                        if task_id:
                            task_manager.fail_task(task_id, error)
                            print(f"❌ [{worker_id}] 任务失败：{task_id} - {error}")
                    
                except WebSocketDisconnect:
                    break
    except WebSocketDisconnect:
        print(f"❌ Worker 断开：{worker_id}")
    except Exception as e:
        print(f"⚠️ Worker 异常：{worker_id} - {e}")
    finally:
        if worker_id:
            # Worker 断线，但不立即注销，保留 5 分钟等待重连
            print(f"⏳ Worker 断线：{worker_id} (保留 5 分钟等待重连)")
            # 将任务状态改为 paused 而不是 failed
            for task_id, task in task_manager.tasks.items():
                if task.get("worker_id") == worker_id and task["status"] == "running":
                    task["status"] = "paused"
                    task["error"] = "Worker 断线，等待重连"
                    task_manager._save_task(task)
            # 5 分钟后如果还没重连，再注销
            asyncio.create_task(_delayed_unregister_worker(worker_id, delay_seconds=300))

async def _delayed_unregister_worker(worker_id: str, delay_seconds: int = 300):
    """延迟注销 Worker - 给重连时间"""
    await asyncio.sleep(delay_seconds)
    if worker_id in task_manager.workers:
        print(f"⏰ Worker 超时未重连：{worker_id}，执行注销")
        task_manager.unregister_worker(worker_id)
    else:
        print(f"✅ Worker 已重连：{worker_id}，跳过注销")

@router.get("/ws/workers")
async def list_workers():
    """列出所有 Worker"""
    workers = []
    for wid, ws in task_manager.workers.items():
        workers.append({
            "worker_id": wid,
            "connected": True,
            "tasks": task_manager.get_worker_tasks(wid)
        })
    return {"workers": workers, "count": len(workers)}

@router.get("/ws/tasks")
async def list_tasks():
    """列出所有任务"""
    return {"tasks": task_manager.get_all_tasks(), "count": len(task_manager.tasks)}

@router.get("/ws/tasks/active")
async def list_active_tasks():
    """列出活动任务"""
    return {"tasks": task_manager.get_active_tasks(), "count": len(task_manager.get_active_tasks())}

@router.get("/ws/stats")
async def get_stats():
    """获取统计信息"""
    return task_manager.get_stats()

@router.get("/ws/dependency/queue/{worker_id}")
async def get_dependency_queue(worker_id: str):
    """获取 Worker 的依赖安装队列状态"""
    return dependency_installer.get_queue_status(worker_id)

@router.get("/ws/dependency/history/{worker_id}")
async def get_dependency_history(worker_id: str, limit: int = 50):
    """获取 Worker 的依赖安装历史"""
    return {"history": dependency_installer.get_history(worker_id, limit)}

@router.post("/ws/worker/command")
async def send_command(command: dict):
    """发送指令到 Worker"""
    worker_id = command.get("worker_id")
    msg_type = command.get("type")
    data = command.get("data", {})
    
    # 处理依赖安装 - 改为逐个下发
    if msg_type == "install_dependencies":
        packages = data.get("packages", [])
        if not packages:
            return {"success": False, "message": "没有指定要安装的包"}
        
        # 添加到队列，启动逐个安装
        dependency_installer.add_packages(worker_id, packages)
        
        # 异步启动安装流程
        asyncio.create_task(dependency_installer.start_installation(worker_id))
        
        return {
            "success": True,
            "message": f"已添加 {len(packages)} 个包到安装队列，将逐个安装",
            "queue_status": dependency_installer.get_queue_status(worker_id)
        }
    
    # 处理单个依赖安装 (内部使用)
    elif msg_type == "install_single":
        package = data.get("package")
        task_id = data.get("task_id", f"install_{package.replace('-', '_')}_{int(time.time())}")
        
        task_manager.create_task(task_id, msg_type, worker_id, data)
        
        message = {"type": msg_type, "data": data, "task_id": task_id}
        
        if worker_id and worker_id in task_manager.workers:
            try:
                ws = task_manager.workers[worker_id]
                await ws.send_json(message)
                return {"success": True, "message": f"指令已发送到 {worker_id}", "task_id": task_id}
            except Exception as e:
                return {"success": False, "message": f"发送失败：{e}", "task_id": task_id}
        else:
            return {"success": False, "message": f"Worker {worker_id} 不在线", "task_id": task_id}
    
    # 其他指令类型
    else:
        task_id = data.get("task_id", f"{msg_type}_{int(datetime.now().timestamp())}")
        task_manager.create_task(task_id, msg_type, worker_id, data)
        
        message = {"type": msg_type, "data": data, "task_id": task_id}
        
        if worker_id and worker_id in task_manager.workers:
            try:
                ws = task_manager.workers[worker_id]
                await ws.send_json(message)
                return {"success": True, "message": f"指令已发送到 {worker_id}", "task_id": task_id}
            except Exception as e:
                return {"success": False, "message": f"发送失败：{e}", "task_id": task_id}
        else:
            # 广播到所有 Worker
            sent_count = 0
            for wid in list(task_manager.workers.keys()):
                try:
                    ws = task_manager.workers[wid]
                    await ws.send_json(message)
                    sent_count += 1
                except:
                    pass
            return {"success": True, "message": f"指令已广播到 {sent_count} 个 Worker", "task_id": task_id}

@router.post("/ws/dependency/cancel/{worker_id}")
async def cancel_dependency_queue(worker_id: str):
    """取消 Worker 的依赖安装队列"""
    cleared = dependency_installer.clear_queue(worker_id)
    return {"success": True, "message": f"清除了 {cleared} 个待安装包"}

@router.patch("/ws/tasks/{task_id}")
async def update_task(task_id: str, update_data: dict):
    """更新任务状态"""
    if task_id in task_manager.tasks:
        task = task_manager.tasks[task_id]
        if "status" in update_data:
            task["status"] = update_data["status"]
        if "error" in update_data:
            task["error"] = update_data["error"]
        if "progress" in update_data:
            task["progress"] = update_data["progress"]
        task["updated_at"] = datetime.now().isoformat()
        if update_data.get("status") == "completed":
            task["completed_at"] = datetime.now().isoformat()
        return {"success": True, "task": task}
    return {"success": False, "error": "Task not found"}

@router.delete("/ws/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id in task_manager.tasks:
        del task_manager.tasks[task_id]
        return {"success": True, "message": f"Task {task_id} deleted"}
    return {"success": False, "error": "Task not found"}

@router.post("/ws/tasks/cleanup")
async def cleanup_old_tasks(days: int = 7):
    """清理旧任务"""
    deleted = task_manager.cleanup_old_tasks(days)
    return {"success": True, "message": f"清理了 {deleted} 个旧任务"}
