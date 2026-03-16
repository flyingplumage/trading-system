"""调度器和任务队列监控 API"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime

from app.schemas.schemas import Response
from app.db import database

# 导入任务队列
try:
    from qframe.scheduler.task_queue import (
        get_task_queue,
        list_training_tasks,
        get_training_task,
        cancel_training_task,
        TaskStatus
    )
    TASK_QUEUE_AVAILABLE = True
except ImportError:
    TASK_QUEUE_AVAILABLE = False

# 导入训练调度器
try:
    from qframe.scheduler import TrainingScheduler, auto_configure_training
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status", response_model=Response)
async def get_scheduler_status():
    """获取调度器状态"""
    if not SCHEDULER_AVAILABLE:
        return Response(
            success=False,
            message="调度器模块未安装",
            data={'available': False}
        )
    
    try:
        scheduler = TrainingScheduler()
        resource_info = scheduler.get_resource_info()
        
        return Response(
            success=True,
            message="OK",
            data={
                'available': True,
                'resource': resource_info,
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=Response)
async def get_recommended_config(
    strategy: str = None,
    total_steps: int = 100000,
    prefer_gpu: bool = True
):
    """获取推荐配置"""
    if not SCHEDULER_AVAILABLE:
        return Response(
            success=False,
            message="调度器模块未安装",
            data={'available': False}
        )
    
    try:
        scheduler = TrainingScheduler()
        config = scheduler.recommend_config(
            strategy=strategy,
            total_steps=total_steps,
            prefer_gpu=prefer_gpu
        )
        
        return Response(
            success=True,
            message="OK",
            data={
                'available': True,
                'config': {
                    'n_envs': config.n_envs,
                    'learning_rate': config.learning_rate,
                    'n_steps': config.n_steps,
                    'batch_size': config.batch_size,
                    'n_epochs': config.n_epochs,
                    'use_gpu': config.use_gpu
                },
                'reason': config.reason
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/status", response_model=Response)
async def get_queue_status():
    """获取任务队列状态"""
    if not TASK_QUEUE_AVAILABLE:
        return Response(
            success=False,
            message="任务队列模块未安装",
            data={'available': False}
        )
    
    try:
        queue = get_task_queue()
        stats = queue.get_stats()
        
        return Response(
            success=True,
            message="OK",
            data={
                'available': True,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/tasks", response_model=Response)
async def get_queue_tasks(
    status: str = None,
    limit: int = 100
):
    """获取队列任务列表"""
    if not TASK_QUEUE_AVAILABLE:
        return Response(
            success=False,
            message="任务队列模块未安装",
            data={'available': False}
        )
    
    try:
        tasks = list_training_tasks(status=status, limit=limit)
        
        return Response(
            success=True,
            message="OK",
            data=tasks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/task/{task_id}", response_model=Response)
async def get_queue_task(task_id: str):
    """获取任务详情"""
    if not TASK_QUEUE_AVAILABLE:
        return Response(
            success=False,
            message="任务队列模块未安装",
            data={'available': False}
        )
    
    try:
        task = get_training_task(task_id)
        
        if task is None:
            return Response(
                success=False,
                message="任务不存在",
                data=None
            )
        
        return Response(
            success=True,
            message="OK",
            data=task.to_dict()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/task/{task_id}/cancel", response_model=Response)
async def cancel_task(task_id: str):
    """取消任务"""
    if not TASK_QUEUE_AVAILABLE:
        return Response(
            success=False,
            message="任务队列模块未安装",
            data={'available': False}
        )
    
    try:
        success = cancel_training_task(task_id)
        
        if success:
            return Response(
                success=True,
                message="任务已取消",
                data={'task_id': task_id}
            )
        else:
            return Response(
                success=False,
                message="任务无法取消（可能已在运行或已完成）",
                data={'task_id': task_id}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 数据库统计（用于 Dashboard）
@router.get("/db/stats", response_model=Response)
async def get_database_stats():
    """获取数据库统计"""
    try:
        stats = database.get_db_stats()
        
        # 添加连接池统计
        read_stats = database.get_read_pool().get_stats()
        write_stats = database.get_write_pool().get_stats()
        queue_stats = database.get_write_queue().get_stats()
        
        return Response(
            success=True,
            message="OK",
            data={
                'database': stats,
                'read_pool': read_stats,
                'write_pool': write_stats,
                'write_queue': queue_stats
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
