"""
Worker 管理 API
管理分布式训练 Worker
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Dict, Optional
from app.schemas.schemas import Response
from app.api.auth import get_current_user_any
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/worker", tags=["worker"])

# Worker 注册表
workers = {}


@router.post("/register", response_model=Response)
async def register_worker(
    worker_info: Dict,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Worker 注册
    
    Args:
        worker_info: Worker 信息
    """
    worker_id = worker_info.get('worker_id')
    
    if not worker_id:
        worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        worker_info['worker_id'] = worker_id
    
    # 记录注册时间
    worker_info['registered_at'] = datetime.now().isoformat()
    worker_info['status'] = 'online'
    worker_info['last_heartbeat'] = datetime.now().isoformat()
    
    workers[worker_id] = worker_info
    
    return Response(
        success=True,
        message="Worker 注册成功",
        data={
            'worker_id': worker_id,
            'status': 'registered'
        }
    )


@router.post("/heartbeat", response_model=Response)
async def worker_heartbeat(
    heartbeat: Dict,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Worker 心跳
    
    Args:
        heartbeat: 心跳信息
    """
    worker_id = heartbeat.get('worker_id')
    
    if not worker_id or worker_id not in workers:
        raise HTTPException(status_code=404, detail="Worker 未注册")
    
    # 更新心跳
    workers[worker_id]['last_heartbeat'] = datetime.now().isoformat()
    workers[worker_id]['status'] = heartbeat.get('status', 'idle')
    workers[worker_id]['resources'] = heartbeat.get('resources', {})
    workers[worker_id]['current_task'] = heartbeat.get('current_task')
    
    return Response(
        success=True,
        message="OK",
        data={'worker_id': worker_id}
    )


@router.post("/offline", response_model=Response)
async def worker_offline(
    data: Dict,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Worker 离线"""
    worker_id = data.get('worker_id')
    
    if worker_id in workers:
        workers[worker_id]['status'] = 'offline'
        workers[worker_id]['last_heartbeat'] = datetime.now().isoformat()
    
    return Response(
        success=True,
        message="OK",
        data={'worker_id': worker_id}
    )


@router.post("/progress/{task_id}", response_model=Response)
async def report_progress(
    task_id: str,
    progress: Dict,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    上报训练进度
    
    Args:
        task_id: 任务 ID
        progress: 进度信息
    """
    # 保存进度到数据库或缓存
    # 这里简化处理
    
    return Response(
        success=True,
        message="进度已接收",
        data={
            'task_id': task_id,
            'progress': progress
        }
    )


@router.post("/result", response_model=Response)
async def report_result(
    result: Dict,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    上报训练结果
    
    Args:
        result: 结果信息
    """
    # 保存结果到数据库
    # 更新任务状态
    
    return Response(
        success=True,
        message="结果已接收",
        data={
            'task_id': result.get('task_id'),
            'status': result.get('status')
        }
    )


@router.post("/upload-model/{task_id}", response_model=Response)
async def upload_model(
    task_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    上传训练模型
    
    Args:
        task_id: 任务 ID
    """
    # 处理文件上传
    # 保存到模型仓库
    
    return Response(
        success=True,
        message="模型已上传",
        data={'task_id': task_id}
    )


@router.get("/list", response_model=Response)
async def list_workers(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user_any)
):
    """
    列出所有 Worker
    
    Args:
        status: 过滤状态 (online/offline/busy/idle)
    """
    worker_list = []
    
    for worker_id, info in workers.items():
        if status is None or info.get('status') == status:
            worker_list.append({
                'worker_id': worker_id,
                'hostname': info.get('hostname'),
                'platform': info.get('platform'),
                'status': info.get('status'),
                'last_heartbeat': info.get('last_heartbeat'),
                'resources': info.get('resources', {}),
                'gpu_info': info.get('gpu_info', {})
            })
    
    return Response(
        success=True,
        message="OK",
        data={
            'total': len(worker_list),
            'workers': worker_list
        }
    )


@router.get("/stats", response_model=Response)
async def get_worker_stats(current_user: dict = Depends(get_current_user_any)):
    """获取 Worker 统计"""
    total = len(workers)
    online = sum(1 for w in workers.values() if w.get('status') == 'online')
    busy = sum(1 for w in workers.values() if w.get('status') == 'busy')
    
    return Response(
        success=True,
        message="OK",
        data={
            'total_workers': total,
            'online_workers': online,
            'busy_workers': busy,
            'idle_workers': online - busy
        }
    )
