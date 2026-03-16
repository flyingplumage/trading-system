"""
训练任务队列服务
管理训练任务的排队、调度、优先级
"""

import threading
import time
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from app.db import database


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 10
    NORMAL = 5
    HIGH = 1


class TaskQueue:
    """训练任务队列"""
    
    def __init__(self, max_concurrent: int = 1):
        self.max_concurrent = max_concurrent
        self.queue: List[Dict] = []
        self.running: Dict[int, Dict] = {}
        self.lock = threading.Lock()
        self.worker_thread = None
        self.running_flag = False
    
    def start(self):
        """启动队列处理器"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running_flag = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """停止队列处理器"""
        self.running_flag = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def add_task(
        self,
        task_id: int,
        strategy: str,
        steps: int,
        priority: int = 5,
        **kwargs
    ) -> int:
        """
        添加任务到队列
        
        Returns:
            队列位置 (1-based)
        """
        with self.lock:
            task = {
                'task_id': task_id,
                'strategy': strategy,
                'steps': steps,
                'priority': priority,
                'kwargs': kwargs,
                'queued_at': datetime.now().isoformat()
            }
            
            # 按优先级插入 (高优先级在前)
            inserted = False
            for i, existing in enumerate(self.queue):
                if priority < existing['priority']:
                    self.queue.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self.queue.append(task)
            
            position = self.queue.index(task) + 1
            return position
    
    def remove_task(self, task_id: int) -> bool:
        """从队列中移除任务"""
        with self.lock:
            for i, task in enumerate(self.queue):
                if task['task_id'] == task_id:
                    self.queue.pop(i)
                    return True
            return False
    
    def get_queue_status(self) -> Dict:
        """获取队列状态"""
        with self.lock:
            return {
                'queued': len(self.queue),
                'running': len(self.running),
                'max_concurrent': self.max_concurrent,
                'queue_tasks': [
                    {
                        'task_id': t['task_id'],
                        'strategy': t['strategy'],
                        'priority': t['priority'],
                        'position': i + 1
                    }
                    for i, t in enumerate(self.queue)
                ],
                'running_tasks': list(self.running.keys())
            }
    
    def get_task_position(self, task_id: int) -> Optional[int]:
        """获取任务在队列中的位置"""
        with self.lock:
            for i, task in enumerate(self.queue):
                if task['task_id'] == task_id:
                    return i + 1
            return None
    
    def _process_queue(self):
        """队列处理主循环"""
        while self.running_flag:
            try:
                with self.lock:
                    # 检查是否有空闲槽位
                    available_slots = self.max_concurrent - len(self.running)
                    
                    if available_slots > 0 and self.queue:
                        # 取出最高优先级的任务
                        task = self.queue.pop(0)
                        self.running[task['task_id']] = task
                
                # 在队列外执行，避免锁竞争
                if task:
                    self._execute_task(task)
                
                time.sleep(1)  # 避免空转
                
            except Exception as e:
                print(f"[Queue] 处理任务失败：{e}")
                time.sleep(5)
    
    def _execute_task(self, task: Dict):
        """执行单个训练任务"""
        task_id = task['task_id']
        
        try:
            print(f"[Queue] 开始执行任务 {task_id}: {task['strategy']}")
            
            # 更新任务状态为 running
            database.update_training_task(task_id, status='running')
            
            # 调用训练器
            from app.services.trainer import trainer
            
            trainer.train(
                strategy=task['strategy'],
                exp_id=f"exp_queue_{task_id}",
                task_id=task_id,
                steps=task['steps'],
                **task.get('kwargs', {})
            )
            
            print(f"[Queue] 任务 {task_id} 完成")
            
        except Exception as e:
            print(f"[Queue] 任务 {task_id} 失败：{e}")
            database.update_training_task(task_id, status='failed', error=str(e))
        
        finally:
            # 从 running 中移除
            with self.lock:
                if task_id in self.running:
                    del self.running[task_id]


# 全局队列实例 (默认并发 1 个训练任务)
task_queue = TaskQueue(max_concurrent=1)
