"""
硬件配置管理 API
配置和调节训练任务的硬件资源
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import Optional, Dict, List
from app.schemas.schemas import Response
from app.services.hardware_config import hardware_config
from app.api.auth import get_current_user_any
from app.api.dependencies import require_user_admin

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.get("/info", response_model=Response)
async def get_hardware_info(current_user: dict = Depends(get_current_user_any)):
    """获取硬件信息"""
    info = hardware_config.get_config()
    
    return Response(
        success=True,
        message="OK",
        data=info
    )


@router.get("/status", response_model=Response)
async def get_hardware_status(current_user: dict = Depends(get_current_user_any)):
    """获取当前硬件使用状态"""
    status = hardware_config.check_resources()
    
    return Response(
        success=True,
        message="OK",
        data=status
    )


@router.get("/config", response_model=Response)
async def get_hardware_config(current_user: dict = Depends(get_current_user_any)):
    """获取硬件配置"""
    config = hardware_config.get_config()
    
    return Response(
        success=True,
        message="OK",
        data=config['config']
    )


@router.post("/config", response_model=Response)
async def update_hardware_config(
    config: Dict = Body(...),
    current_user: dict = Depends(get_current_user_any)
):
    """
    更新硬件配置
    
    Args:
        config: 配置信息
    """
    result = hardware_config.update_config(config)
    
    return Response(
        success=True,
        message="配置已更新",
        data=result['config']
    )


@router.post("/config/reset", response_model=Response)
async def reset_hardware_config(current_user: dict = Depends(get_current_user_any)):
    """重置硬件配置为默认值"""
    default_config = {
        'cpu': {
            'max_cores': -1,
            'max_percent': 80,
            'affinity': []
        },
        'memory': {
            'max_gb': -1,
            'max_percent': 80,
            'swap_allowed': False
        },
        'gpu': {
            'enabled': True,
            'device_ids': [],
            'memory_fraction': 0.8,
            'allow_growth': True,
            'mixed_precision': False
        },
        'disk': {
            'max_use_percent': 90,
            'temp_dir': '/tmp/training',
            'checkpoint_dir': './checkpoints'
        },
        'training': {
            'max_concurrent_tasks': 1,
            'default_batch_size': 64,
            'default_learning_rate': 3e-5,
            'early_stopping': True,
            'patience': 10
        }
    }
    
    result = hardware_config.update_config(default_config)
    
    return Response(
        success=True,
        message="配置已重置",
        data=result['config']
    )


@router.get("/recommend", response_model=Response)
async def get_recommended_config(
    strategy: str = Query(default='auto', description="策略类型"),
    current_user: dict = Depends(get_current_user_any)
):
    """获取推荐的硬件配置"""
    result = hardware_config.get_optimal_config(strategy=strategy)
    
    return Response(
        success=True,
        message="OK",
        data=result
    )


@router.post("/apply/{task_id}", response_model=Response)
async def apply_hardware_limits(
    task_id: str,
    current_user: dict = Depends(get_current_user_any)
):
    """
    应用硬件限制到训练任务
    
    Args:
        task_id: 任务 ID
    """
    applied = hardware_config.apply_limits(task_id)
    
    return Response(
        success=True,
        message="硬件限制已应用",
        data=applied
    )


@router.get("/gpu/list", response_model=Response)
async def list_gpu_devices(current_user: dict = Depends(get_current_user_any)):
    """列出 GPU 设备"""
    gpu_info = hardware_config.system_info['gpu']
    
    return Response(
        success=True,
        message="OK",
        data=gpu_info
    )


@router.post("/gpu/select", response_model=Response)
async def select_gpu_devices(
    device_ids: List[int] = Body(..., description="GPU 设备 ID 列表"),
    current_user: dict = Depends(get_current_user_any)
):
    """
    选择使用的 GPU 设备
    
    Args:
        device_ids: GPU 设备 ID 列表
    """
    config = hardware_config.update_config({
        'gpu': {
            'device_ids': device_ids
        }
    })
    
    return Response(
        success=True,
        message=f"已选择 GPU: {device_ids}",
        data=config['config']['gpu']
    )


@router.get("/limits", response_model=Response)
async def get_hardware_limits(current_user: dict = Depends(get_current_user_any)):
    """获取硬件限制配置"""
    config = hardware_config.config
    
    limits = {
        'cpu': {
            'max_cores': config['cpu']['max_cores'],
            'max_percent': config['cpu']['max_percent']
        },
        'memory': {
            'max_gb': config['memory']['max_gb'],
            'max_percent': config['memory']['max_percent']
        },
        'gpu': {
            'enabled': config['gpu']['enabled'],
            'memory_fraction': config['gpu']['memory_fraction']
        },
        'disk': {
            'max_use_percent': config['disk']['max_use_percent']
        }
    }
    
    return Response(
        success=True,
        message="OK",
        data=limits
    )


@router.post("/limits", response_model=Response)
async def update_hardware_limits(
    limits: Dict = Body(...),
    current_user: dict = Depends(get_current_user_any)
):
    """
    更新硬件限制
    
    Args:
        limits: 限制配置
    """
    result = hardware_config.update_config(limits)
    
    return Response(
        success=True,
        message="限制已更新",
        data={
            'cpu': result['config']['cpu'],
            'memory': result['config']['memory'],
            'gpu': result['config']['gpu'],
            'disk': result['config']['disk']
        }
    )
