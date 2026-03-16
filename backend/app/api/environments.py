"""交易环境管理 API"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.schemas import Response
from app.env import list_envs, get_env_class

router = APIRouter(prefix="/api/environments", tags=["environments"])


@router.get("", response_model=Response)
async def list_environments():
    """获取所有可用环境"""
    try:
        envs = list_envs()
        
        env_info = []
        for env_name in envs:
            EnvClass = get_env_class(env_name)
            desc = EnvClass.__doc__ or ''
            if '\n' in desc:
                desc = desc.split('\n')[1].strip()
            env_info.append({
                'name': env_name,
                'class': EnvClass.__name__,
                'description': desc
            })
        
        return Response(
            success=True,
            message="OK",
            data=env_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{env_name}", response_model=Response)
async def get_environment(env_name: str):
    """获取环境详情"""
    try:
        EnvClass = get_env_class(env_name)
        
        return Response(
            success=True,
            message="OK",
            data={
                'name': env_name,
                'class': EnvClass.__name__,
                'description': EnvClass.__doc__,
                'params': {
                    'window_size': 20,
                    'initial_cash': 1000000,
                    'commission_rate': 0.0003,
                    'slippage': 0.001,
                }
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
