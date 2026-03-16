"""
模型解释 API
使用 SHAP 和 LIME 解释模型决策
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, List
from app.schemas.schemas import Response
from app.services.explanation import model_explainer
from app.api.dependencies import require_model_read, require_model_create
import numpy as np

router = APIRouter(prefix="/api/models/explain", tags=["models-explain"])


@router.post("/shap", response_model=Response)
async def explain_with_shap(
    model_id: str = Body(...),
    n_samples: int = Body(default=100, ge=10, le=500),
    current_user: dict = Depends(require_model_read)
):
    """
    使用 SHAP 解释模型
    
    Args:
        model_id: 模型 ID
        n_samples: 样本数
    """
    try:
        from app.services.model import model_service
        from app.services.data import DataService
        
        # 获取模型
        model_info = model_service.get_model(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 加载模型
        model = model_service.load_model(model_id)
        
        # 获取训练数据
        data_service = DataService()
        X_train = data_service.get_features('000001.SZ', limit=500)
        
        if X_train is None or len(X_train) == 0:
            # 生成示例数据
            X_train = np.random.randn(100, 10)
        
        # SHAP 解释
        result = model_explainer.explain_with_shap(
            model=model,
            X_train=X_train,
            X_test=X_train,
            n_samples=n_samples
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return Response(
            success=True,
            message="SHAP 解释完成",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lime", response_model=Response)
async def explain_with_lime(
    model_id: str = Body(...),
    instance_idx: int = Body(default=0, ge=0, le=100),
    n_features: int = Body(default=5, ge=1, le=10),
    current_user: dict = Depends(require_model_read)
):
    """
    使用 LIME 解释单个预测
    
    Args:
        model_id: 模型 ID
        instance_idx: 样本索引
        n_features: 显示的特征数
    """
    try:
        from app.services.model import model_service
        from app.services.data import DataService
        
        # 获取模型
        model_info = model_service.get_model(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 加载模型
        model = model_service.load_model(model_id)
        
        # 获取数据
        data_service = DataService()
        X_train = data_service.get_features('000001.SZ', limit=200)
        
        if X_train is None or len(X_train) == 0:
            X_train = np.random.randn(100, 10)
        
        # 获取单个样本
        instance = X_train[instance_idx:instance_idx+1]
        
        # LIME 解释
        result = model_explainer.explain_with_lime(
            model=model,
            X_train=X_train,
            instance=instance,
            n_features=n_features
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return Response(
            success=True,
            message="LIME 解释完成",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-importance/{model_id}", response_model=Response)
async def get_feature_importance(
    model_id: str,
    method: str = Query(default='shap', enum=['shap', 'permutation']),
    current_user: dict = Depends(require_model_read)
):
    """
    获取特征重要性
    
    Args:
        model_id: 模型 ID
        method: 解释方法
    """
    try:
        from app.services.model import model_service
        from app.services.data import DataService
        
        # 获取模型
        model_info = model_service.get_model(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 加载模型
        model = model_service.load_model(model_id)
        
        # 获取数据
        data_service = DataService()
        X_train = data_service.get_features('000001.SZ', limit=200)
        
        if X_train is None or len(X_train) == 0:
            X_train = np.random.randn(100, 10)
        
        # 特征重要性
        result = model_explainer.explain_feature_importance(
            model=model,
            X_train=X_train,
            method=method
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return Response(
            success=True,
            message="特征重要性分析完成",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision-boundary/{model_id}", response_model=Response)
async def get_decision_boundary(
    model_id: str,
    feature1: int = Query(default=0, ge=0, le=9),
    feature2: int = Query(default=1, ge=0, le=9),
    current_user: dict = Depends(require_model_read)
):
    """
    获取决策边界
    
    Args:
        model_id: 模型 ID
        feature1: 第一个特征索引
        feature2: 第二个特征索引
    """
    try:
        from app.services.model import model_service
        from app.services.data import DataService
        
        # 获取模型
        model_info = model_service.get_model(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 加载模型
        model = model_service.load_model(model_id)
        
        # 获取数据
        data_service = DataService()
        X_train = data_service.get_features('000001.SZ', limit=200)
        
        if X_train is None or len(X_train) == 0:
            X_train = np.random.randn(100, 10)
        
        # 决策边界
        result = model_explainer.explain_decision_boundary(
            model=model,
            X_train=X_train,
            feature1_idx=feature1,
            feature2_idx=feature2
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return Response(
            success=True,
            message="决策边界分析完成",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/methods", response_model=Response)
async def list_explanation_methods(current_user: dict = Depends(require_model_read)):
    """列出所有解释方法"""
    from app.services.explanation import SHAP_AVAILABLE, LIME_AVAILABLE
    
    methods = {
        'shap': {
            'name': 'SHAP',
            'description': '基于博弈论的模型解释方法',
            'available': SHAP_AVAILABLE,
            'install': 'pip install shap'
        },
        'lime': {
            'name': 'LIME',
            'description': '局部可解释的模型无关解释',
            'available': LIME_AVAILABLE,
            'install': 'pip install lime'
        },
        'permutation': {
            'name': '排列重要性',
            'description': '基于特征置换的重要性分析',
            'available': True,
            'install': None
        }
    }
    
    return Response(
        success=True,
        message="OK",
        data={
            'total_methods': len(methods),
            'methods': methods
        }
    )
