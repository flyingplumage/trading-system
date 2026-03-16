"""训练服务 API - 真实 PPO 训练 (支持队列)"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import List, Optional
from app.db import database
from app.schemas.schemas import TrainingTaskCreate, TrainingTask, Response
from app.services.trainer import trainer
from app.services.queue import task_queue
from app.api.dependencies import require_train_read, require_train_create
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/train", tags=["training"])

# 训练任务状态
training_tasks = {}

@router.post("/start", response_model=Response)
async def start_training(
    strategy: str,
    steps: int = 10000,
    priority: int = 5,
    env_name: str = 'momentum',
    stock_code: str = '000001.SZ',
    learning_rate: float = 3e-5,
    use_queue: bool = True,
    current_user: dict = Depends(require_train_create)
):
    """
    启动 PPO 训练
    
    Args:
        strategy: 策略名称
        steps: 训练步数
        priority: 优先级 (1-10, 1 最高)
        env_name: 环境名称
        stock_code: 股票代码
        learning_rate: 学习率
        use_queue: 是否使用队列 (默认 True)
    """
    
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
        priority=priority
    )
    
    if use_queue:
        # 加入队列
        position = task_queue.add_task(
            task_id=task_id,
            strategy=strategy,
            steps=steps,
            priority=priority,
            learning_rate=learning_rate,
            env_name=env_name,
            stock_code=stock_code
        )
        
        return Response(
            success=True,
            message="训练任务已加入队列",
            data={
                'task_id': task_id,
                'experiment_id': exp_id,
                'queue_position': position,
                'mode': 'queued'
            }
        )
    else:
        # 直接后台执行
        def run_real_training():
            try:
                trainer.train(
                    strategy=strategy,
                    exp_id=exp_id,
                    task_id=task_id,
                    steps=steps,
                    learning_rate=learning_rate,
                    env_name=env_name,
                    stock_code=stock_code
                )
            except Exception as e:
                print(f"训练失败：{e}")
                database.update_training_task(task_id, status='failed', error=str(e))
        
        background_tasks = BackgroundTasks()
        background_tasks.add_task(run_real_training)
        
        return Response(
            success=True,
            message="PPO 训练已启动",
            data={
                'task_id': task_id,
                'experiment_id': exp_id,
                'mode': 'direct'
            }
        )

@router.get("/status/{task_id}", response_model=Response)
async def get_training_status(task_id: int, current_user: dict = Depends(require_train_read)):
    """获取训练状态"""
    task = database.get_training_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取实验进度
    exp_metrics = {}
    if task.get('experiment_id'):
        exp = database.get_experiment(task['experiment_id'])
        if exp:
            exp_metrics = exp.get('metrics', {})
    
    return Response(
        success=True,
        message="OK",
        data={
            **task,
            'progress': exp_metrics.get('progress', 0)
        }
    )

@router.get("/tasks", response_model=Response)
async def list_training_tasks(status: str = None, limit: int = 100, current_user: dict = Depends(require_train_read)):
    """获取训练任务列表"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute(
                'SELECT * FROM training_tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?',
                [status, limit]
            )
        else:
            cursor.execute('SELECT * FROM training_tasks ORDER BY created_at DESC LIMIT ?', [limit])
        tasks = [dict(row) for row in cursor.fetchall()]
    
    return Response(success=True, message="OK", data=tasks)
