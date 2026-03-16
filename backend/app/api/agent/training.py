"""
智能体训练监控 API
提供训练进度、指标、日志等数据
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from app.db import database
from app.schemas.schemas import Response
from pathlib import Path
import json

router = APIRouter(prefix="/api/agent/training", tags=["Agent-Training"])

@router.get("/status", response_model=Response)
async def get_training_status():
    """获取训练系统整体状态"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 统计训练任务
        cursor.execute("SELECT status, COUNT(*) FROM training_tasks GROUP BY status")
        task_stats = dict(cursor.fetchall())
        
        # 获取运行中的训练
        cursor.execute("""
            SELECT id, strategy, steps, created_at 
            FROM training_tasks 
            WHERE status = 'running'
            ORDER BY created_at DESC
        """)
        running_tasks = [
            {'id': row[0], 'strategy': row[1], 'steps': row[2], 'created_at': row[3]}
            for row in cursor.fetchall()
        ]
        
        # 获取实验统计
        cursor.execute("SELECT COUNT(*) FROM experiments WHERE status = 'completed'")
        completed_experiments = cursor.fetchone()[0]
    
    return Response(
        success=True,
        message="OK",
        data={
            'task_stats': task_stats,
            'running_tasks': running_tasks,
            'completed_experiments': completed_experiments
        }
    )

@router.get("/{task_id}/progress", response_model=Response)
async def get_training_progress(task_id: int):
    """获取训练进度详情"""
    task = database.get_training_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取实验指标
    exp_metrics = {}
    if task.get('experiment_id'):
        exp = database.get_experiment(task['experiment_id'])
        if exp:
            exp_metrics = exp.get('metrics', {})
    
    # 计算进度
    steps = task.get('steps', 0)
    current_step = exp_metrics.get('step', 0)
    progress = (current_step / steps * 100) if steps > 0 else 0
    
    return Response(
        success=True,
        message="OK",
        data={
            'task_id': task_id,
            'status': task.get('status'),
            'progress': progress,
            'current_step': current_step,
            'total_steps': steps,
            'metrics': exp_metrics,
            'result': task.get('result'),
            'error': task.get('error')
        }
    )

@router.get("/{task_id}/metrics", response_model=Response)
async def get_training_metrics(task_id: int):
    """获取训练指标时间序列"""
    task = database.get_training_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取实验数据
    if not task.get('experiment_id'):
        return Response(success=True, message="无实验数据", data={'metrics': []})
    
    exp = database.get_experiment(task['experiment_id'])
    if not exp:
        return Response(success=True, message="无实验数据", data={'metrics': []})
    
    # 解析指标
    metrics = exp.get('metrics', {})
    
    return Response(
        success=True,
        message="OK",
        data={
            'task_id': task_id,
            'metrics': metrics,
            'portfolio_value': metrics.get('portfolio_value', 0),
            'cash': metrics.get('cash', 0),
            'step': metrics.get('step', 0),
            'progress': metrics.get('progress', 0)
        }
    )

@router.get("/{task_id}/logs", response_model=Response)
async def get_training_logs(task_id: int, lines: int = 100):
    """获取训练日志"""
    task = database.get_training_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 读取日志文件
    log_path = Path(__file__).parent.parent.parent.parent / "logs" / f"training_{task_id}.log"
    
    logs = []
    if log_path.exists():
        with open(log_path) as f:
            logs = f.readlines()[-lines:]
    
    return Response(
        success=True,
        message="OK",
        data={
            'task_id': task_id,
            'logs': logs,
            'total_lines': len(logs)
        }
    )

@router.post("/{task_id}/stop", response_model=Response)
async def stop_training(task_id: int):
    """停止训练任务"""
    task = database.get_training_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新任务状态
    database.update_training_task(
        task_id=task_id,
        status='stopped',
        error='用户手动停止'
    )
    
    return Response(
        success=True,
        message="训练已停止",
        data={'task_id': task_id}
    )

@router.get("/history/list", response_model=Response)
async def get_training_history(limit: int = 50):
    """获取训练历史"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, strategy, steps, status, created_at, completed_at, result
            FROM training_tasks
            ORDER BY created_at DESC
            LIMIT ?
        """, [limit])
        
        history = [
            {
                'task_id': row[0],
                'strategy': row[1],
                'steps': row[2],
                'status': row[3],
                'created_at': row[4],
                'completed_at': row[5],
                'result': json.loads(row[6]) if row[6] else {}
            }
            for row in cursor.fetchall()
        ]
    
    return Response(success=True, message="OK", data=history)
