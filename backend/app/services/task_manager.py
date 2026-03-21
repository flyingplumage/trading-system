"""任务管理器 - 服务端统一管理所有任务进度 (支持 SQLite 持久化)"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import threading

class TaskManager:
    """管理所有 Worker 的任务"""
    
    def __init__(self, db_path: str = "data/tasks.db"):
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._db_lock = threading.Lock()
        
        # 任务队列：{task_id: task_info}
        self.tasks: Dict[str, dict] = {}
        # Worker 连接：{worker_id: websocket}
        self.workers: Dict[str, object] = {}
        # Worker 任务进度：{worker_id: {task_id: progress_info}}
        self.worker_progress: Dict[str, dict] = {}
        
        # 初始化数据库
        self._init_db()
        # 加载已有任务
        self._load_tasks_from_db()
    
    def _init_db(self):
        """初始化数据库表结构 + 性能索引"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    worker_id TEXT,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    data TEXT,
                    result TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    version TEXT,
                    status TEXT,
                    last_seen TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            # 性能优化索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_status 
                ON tasks(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_worker 
                ON tasks(worker_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_created 
                ON tasks(created_at DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_type 
                ON tasks(task_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_workers_status 
                ON workers(status)
            ''')
            conn.commit()
            conn.close()
            print(f"💾 任务数据库已初始化：{self.db_path}")
            print(f"📊 数据库索引已创建 (5 个)")
    
    def _load_tasks_from_db(self):
        """从数据库加载未完成的任务"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE status IN ('pending', 'running')
                ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                task = {
                    "task_id": row[0],
                    "task_type": row[1],
                    "worker_id": row[2],
                    "status": row[3],
                    "progress": row[4],
                    "data": json.loads(row[5]) if row[5] else {},
                    "result": json.loads(row[6]) if row[6] else None,
                    "error": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                    "completed_at": row[10]
                }
                self.tasks[task["task_id"]] = task
            
            print(f"📂 从数据库加载了 {len(self.tasks)} 个未完成任务")
    
    def _save_task(self, task: dict):
        """保存任务到数据库"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (task_id, task_type, worker_id, status, progress, data, result, error, 
                 created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task["task_id"],
                task["task_type"],
                task["worker_id"],
                task["status"],
                task["progress"],
                json.dumps(task["data"], ensure_ascii=False),
                json.dumps(task["result"], ensure_ascii=False) if task["result"] else None,
                task["error"],
                task["created_at"],
                task["updated_at"],
                task["completed_at"]
            ))
            conn.commit()
            conn.close()
    
    def _save_worker(self, worker_id: str, version: str = None, status: str = None):
        """保存 Worker 信息到数据库"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO workers 
                (worker_id, version, status, last_seen, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (
                worker_id,
                version,
                status or "connected",
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
    
    def create_task(self, task_id: str, task_type: str, worker_id: str = None, data: dict = None):
        """创建新任务"""
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "worker_id": worker_id,
            "status": "pending",
            "progress": 0,
            "data": data or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None,
            "result": None
        }
        
        self.tasks[task_id] = task
        self._save_task(task)  # 持久化到数据库
        
        print(f"📋 创建任务：{task_id} ({task_type})")
        return task
    
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
        
        self._save_task(task)  # 持久化到数据库
        
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
            task = self.tasks[task_id]
            task["status"] = "failed"
            task["error"] = error
            task["updated_at"] = datetime.now().isoformat()
            self._save_task(task)
            print(f"❌ 任务失败：{task_id} - {error}")
    
    def register_worker(self, worker_id: str, websocket, version: str = None):
        """注册 Worker"""
        self.workers[worker_id] = websocket
        self.worker_progress[worker_id] = {}
        self._save_worker(worker_id, version, "connected")
        print(f"✅ Worker 已注册：{worker_id} (v{version})")
    
    def unregister_worker(self, worker_id: str):
        """注销 Worker"""
        if worker_id in self.workers:
            del self.workers[worker_id]
        if worker_id in self.worker_progress:
            del self.worker_progress[worker_id]
        self._save_worker(worker_id, status="disconnected")
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
        import asyncio
        from starlette.websockets import WebSocket
        
        message = {
            "type": "task_update",
            "task": task
        }
        
        for worker_id, ws in list(self.workers.items()):
            try:
                asyncio.create_task(ws.send_json(message))
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
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """获取单个任务"""
        return self.tasks.get(task_id)
    
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
    
    def cleanup_old_tasks(self, days: int = 7):
        """清理 N 天前的已完成任务"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        to_delete = []
        
        for task_id, task in self.tasks.items():
            if task["status"] in ["completed", "failed"]:
                try:
                    completed_at = datetime.fromisoformat(task["completed_at"] or task["updated_at"])
                    if completed_at < cutoff:
                        to_delete.append(task_id)
                except:
                    pass
        
        for task_id in to_delete:
            del self.tasks[task_id]
        
        # 清理数据库
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM tasks 
                WHERE status IN ('completed', 'failed') 
                AND completed_at < ?
            ''', (cutoff.isoformat(),))
            conn.commit()
            conn.close()
        
        print(f"🧹 清理了 {len(to_delete)} 个旧任务")
        return len(to_delete)

# 全局实例
task_manager = TaskManager()
