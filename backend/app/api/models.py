"""模型管理 API（使用服务层）"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from typing import List
from app.schemas.schemas import ModelRegister, Model, Response
from app.services.model import ModelService
from app.services.exceptions import NotFoundError, ValidationError, InternalError
import hashlib
from pathlib import Path
import json

router = APIRouter(prefix="/api/models", tags=["models"])

# 服务实例
model_service = ModelService()

MODELS_DIR = Path(__file__).parent.parent.parent / "shared" / "models" / "registered"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=Response)
async def list_models(strategy: str = None, experiment_id: str = None, limit: int = 100):
    """获取模型列表"""
    try:
        models = model_service.list(
            strategy=strategy,
            experiment_id=experiment_id,
            limit=limit
        )
        return Response(success=True, message="OK", data=models)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best", response_model=Response)
async def get_best_models(strategy: str = None, limit: int = 10):
    """获取最佳模型"""
    try:
        models = model_service.get_best(strategy=strategy, limit=limit)
        return Response(success=True, message="OK", data=models)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", response_model=Response)
async def get_model(model_id: str):
    """获取模型详情"""
    try:
        model = model_service.get(model_id)
        return Response(success=True, message="OK", data=model)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", response_model=Response)
async def register_model(model: ModelRegister):
    """注册模型"""
    try:
        created = model_service.create(
            name=model.name,
            strategy=model.strategy,
            experiment_id=model.experiment_id,
            model_path=model.model_path,
            metrics=model.metrics,
            tags=model.tags if hasattr(model, 'tags') else None
        )
        return Response(success=True, message="模型注册成功", data=created)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=Response)
async def upload_model(
    file: UploadFile = File(...),
    name: str = ...,
    strategy: str = ...,
    experiment_id: str = ...,
    metrics: str = None
):
    """上传并注册模型"""
    try:
        # 保存模型文件
        model_path = MODELS_DIR / f"{strategy.replace('/', '_')}_{file.filename}"
        with open(model_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # 计算哈希
        model_hash = hashlib.sha256(open(model_path, "rb").read()).hexdigest()[:16]
        
        # 注册模型
        created = model_service.create(
            name=name,
            strategy=strategy,
            experiment_id=experiment_id,
            model_path=str(model_path),
            metrics=json.loads(metrics) if metrics else {},
            tags=None
        )
        return Response(success=True, message="模型上传成功", data=created)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
