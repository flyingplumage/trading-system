"""
训练任务队列 API
管理训练任务的排队、调度
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
from app.db import database
from app.schemas.schemas import Response
from app.services.queue import task_queue
from app.services.trainer import trainer
from app.api.dependencies import require_queue_config, require_train_read, require_train_create
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/queue", tags=["queue"])

# 启动队列处理器
task_queue.start()

@router.post("/enqueue", response_model=Response)
async def enqueue_task(
    strategy: str,
    steps: int = 10000,
    priority: str = 'normal',  # low, normal, high
    env_name: str = 'momentum',
    stock_code: str = '000001.SZ',
    learning_rate: float = 3e-5,
    current_user: dict = Depends(require_train_create)
):
    """
    将训练任务加入队列
    
    Args:
        strategy: 策略名称
        steps: 训练步数
        priority: 优先级 (low/normal/high)
        env_name: 环境名称
        stock_code: 股票代码
        learning_rate: 学习率
    """
    
    # 优先级映射
    priority_map = {
        'low': 10,
        'normal': 5,
        'high': 1
    }
    priority_value = priority_map.get(priority.lower(), 5)
    
    # 创建实验
    exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    database.create_experiment(
        exp_id=exp_id,
        name=f"{strategy}_train",
        strategy=strategy,
        config={'steps': steps, 'learning_rate': learning_rate}
    )
    
    # 创建训练任务
    task_id = database.create_training_task(
        strategy=strategy,
        steps=steps,
        priority=priority_value
    )
    
    # 加入队列
    position = task_queue.add_task(
        task_id=task_id,
        strategy=strategy,
        steps=steps,
        priority=priority_value,
        learning_rate=learning_rate,
        env_name=env_name,
        stock_code=stock_code
    )
    
    return Response(
        success=True,
        message="任务已加入队列",
        data={
            'task_id': task_id,
            'experiment_id': exp_id,
            'position': position,
            'priority': priority
        }
    )

@router.get("/status", response_model=Response)
async def get_queue_status(current_user: dict = Depends(require_train_read)):
    """获取队列状态"""
    status = task_queue.get_queue_status()
    return Response(
        success=True,
        message="OK",
        data=status
    )

@router.get("/position/{task_id}", response_model=Response)
async def get_task_position(task_id: int, current_user: dict = Depends(require_train_read)):
    """获取任务在队列中的位置"""
    position = task_queue.get_task_position(task_id)
    
    if position is None:
        # 检查是否正在运行
        running = task_queue.get_queue_status()['running_tasks']
        if task_id in running:
            return Response(
                success=True,
                message="任务正在运行",
                data={'task_id': task_id, 'status': 'running'}
            )
        else:
            raise HTTPException(status_code=404, detail="任务不在队列中")
    
    return Response(
        success=True,
        message="OK",
        data={
            'task_id': task_id,
            'position': position
        }
    )

@router.post("/cancel/{task_id}", response_model=Response)
async def cancel_task(task_id: int, current_user: dict = Depends(require_train_create)):
    """取消队列中的任务"""
    removed = task_queue.remove_task(task_id)
    
    if not removed:
        raise HTTPException(status_code=404, detail="任务不在队列中")
    
    # 更新任务状态
    database.update_training_task(task_id, status='cancelled')
    
    return Response(
        success=True,
        message="任务已取消",
        data={'task_id': task_id}
    )

@router.post("/config", response_model=Response)
async def configure_queue(max_concurrent: int = 1, current_user: dict = Depends(require_queue_config)):
    """
    配置队列参数
    
    Args:
        max_concurrent: 最大并发训练任务数
    """
    # 停止当前队列
    task_queue.stop()
    
    # 重新配置
    task_queue.max_concurrent = max_concurrent
    
    # 重启队列
    task_queue.start()
    
    return Response(
        success=True,
        message=f"队列配置已更新：最大并发={max_concurrent}",
        data={'max_concurrent': max_concurrent}
    )

@router.get("/tasks", response_model=Response)
async def list_queue_tasks(status: str = None, current_user: dict = Depends(require_train_read)):
    """
    获取队列任务列表
    
    Args:
        status: 过滤状态 (queued/running)
    """
    queue_status = task_queue.get_queue_status()
    
    if status == 'queued':
        tasks = queue_status['queue_tasks']
    elif status == 'running':
        tasks = [{'task_id': tid} for tid in queue_status['running_tasks']]
    else:
        tasks = {
            'queued': queue_status['queue_tasks'],
            'running': [{'task_id': tid} for tid in queue_status['running_tasks']]
        }
    
    return Response(
        success=True,
        message="OK",
        data=tasks
    )
