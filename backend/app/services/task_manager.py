"""任务管理器 - 服务端统一管理所有任务进度"""
import json
from datetime import datetime
from typing import Dict, List, Optional

class TaskManager:
    """管理所有 Worker 的任务"""
    
    def __init__(self):
        # 任务队列：{task_id: task_info}
        self.tasks: Dict[str, dict] = {}
        # Worker 连接：{worker_id: websocket}
        self.workers: Dict[str, object] = {}
        # Worker 任务进度：{worker_id: {task_id: progress_info}}
        self.worker_progress: Dict[str, dict] = {}
    
    def create_task(self, task_id: str, task_type: str, worker_id: str = None, data: dict = None):
        """创建新任务"""
        self.tasks[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "worker_id": worker_id,
            "status": "pending",
            "progress": 0,
            "data": data or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None
        }
        print(f"📋 创建任务：{task_id} ({task_type})")
        return self.tasks[task_id]
    
    def update_task_progress(self, task_id: str, progress: int, status: str = "running", extra_data: dict = None):
        """更新任务进度"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task["progress"] = progress
        task["status"] = status
        task["updated_at"] = datetime.now().isoformat()
        
        if extra_data:
            task.update(extra_data)
        
        if progress >= 100 and status == "completed":
            task["completed_at"] = datetime.now().isoformat()
        
        print(f"📊 任务进度：{task_id} - {progress}% ({status})")
        
        # 广播给所有 Worker
        self.broadcast_task_update(task)
    
    def complete_task(self, task_id: str, result: dict = None):
        """完成任务"""
        self.update_task_progress(task_id, 100, "completed", {"result": result})
        print(f"✅ 任务完成：{task_id}")
    
    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = error
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
            print(f"❌ 任务失败：{task_id} - {error}")
    
    def register_worker(self, worker_id: str, websocket):
        """注册 Worker"""
        self.workers[worker_id] = websocket
        self.worker_progress[worker_id] = {}
        print(f"✅ Worker 已注册：{worker_id}")
    
    def unregister_worker(self, worker_id: str):
        """注销 Worker"""
        if worker_id in self.workers:
            del self.workers[worker_id]
        if worker_id in self.worker_progress:
            del self.worker_progress[worker_id]
        print(f"❌ Worker 已注销：{worker_id}")
    
    def update_worker_progress(self, worker_id: str, task_id: str, progress: int, status: str = "running", extra_data: dict = None):
        """更新 Worker 任务进度"""
        if worker_id not in self.worker_progress:
            self.worker_progress[worker_id] = {}
        
        self.worker_progress[worker_id][task_id] = {
            "progress": progress,
            "status": status,
            "updated_at": datetime.now().isoformat(),
            **(extra_data or {})
        }
        
        # 同步到任务管理器
        if task_id in self.tasks:
            self.update_task_progress(task_id, progress, status, extra_data)
    
    def broadcast_task_update(self, task: dict):
        """广播任务更新给所有 Worker"""
        message = {
            "type": "task_update",
            "task": task
        }
        message_str = json.dumps(message)
        
        for worker_id, ws in list(self.workers.items()):
            try:
                import asyncio
                # FastAPI WebSocket.send() 需要字符串
                asyncio.create_task(ws.send(message_str))
            except Exception as e:
                print(f"广播失败 {worker_id}: {e}")
    
    def get_all_tasks(self) -> List[dict]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_active_tasks(self) -> List[dict]:
        """获取活动任务"""
        return [t for t in self.tasks.values() if t["status"] in ["pending", "running"]]
    
    def get_worker_tasks(self, worker_id: str) -> List[dict]:
        """获取 Worker 的任务"""
        return [t for t in self.tasks.values() if t.get("worker_id") == worker_id]
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks.values() if t["status"] == "completed"])
        running = len([t for t in self.tasks.values() if t["status"] == "running"])
        failed = len([t for t in self.tasks.values() if t["status"] == "failed"])
        pending = len([t for t in self.tasks.values() if t["status"] == "pending"])
        
        return {
            "total_tasks": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "pending": pending,
            "workers": len(self.workers)
        }

# 全局实例
task_manager = TaskManager()
