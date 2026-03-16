"""实验管理 API（使用服务层）"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.schemas import ExperimentCreate, ExperimentUpdate, Experiment, Response
from app.services.experiment import ExperimentService
from app.services.exceptions import NotFoundError, ValidationError, InternalError

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

# 服务实例
experiment_service = ExperimentService()


@router.get("", response_model=Response)
async def list_experiments(status: str = None, strategy: str = None, limit: int = 100):
    """获取实验列表"""
    try:
        experiments = experiment_service.list(
            status=status,
            strategy=strategy,
            limit=limit
        )
        return Response(success=True, message="OK", data=experiments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{exp_id}", response_model=Response)
async def get_experiment(exp_id: str):
    """获取实验详情"""
    try:
        exp = experiment_service.get(exp_id)
        return Response(success=True, message="OK", data=exp)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=Response)
async def create_experiment(exp: ExperimentCreate):
    """创建实验"""
    try:
        created = experiment_service.create(
            name=exp.name,
            strategy=exp.strategy,
            config=exp.config,
            tags=exp.tags if hasattr(exp, 'tags') else None
        )
        return Response(success=True, message="实验创建成功", data=created)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{exp_id}", response_model=Response)
async def update_experiment(exp_id: str, exp: ExperimentUpdate):
    """更新实验"""
    try:
        update_data = {k: v for k, v in exp.model_dump().items() if v is not None}
        updated = experiment_service.update(exp_id, **update_data)
        return Response(success=True, message="实验更新成功", data=updated)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{exp_id}", response_model=Response)
async def delete_experiment(exp_id: str):
    """删除实验"""
    try:
        experiment_service.delete(exp_id)
        return Response(success=True, message="实验删除成功")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", response_model=Response)
async def get_experiment_stats():
    """获取实验统计"""
    try:
        stats = experiment_service.get_stats()
        return Response(success=True, message="OK", data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
