"""
模型服务类
负责模型的 CRUD 操作和业务逻辑
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import ServiceBase
from .exceptions import NotFoundError, ValidationError, InternalError
from app.db import (
    create_model,
    list_models,
    get_best_models,
)


class ModelService(ServiceBase):
    """模型服务类"""
    
    def __init__(self):
        super().__init__()
        self.models_dir = Path(__file__).parent.parent.parent / "shared" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.log_info("ModelService 初始化")
    
    def list(
        self,
        strategy: str = None,
        experiment_id: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取模型列表
        
        Args:
            strategy: 策略过滤
            experiment_id: 实验 ID 过滤
            limit: 数量限制
        
        Returns:
            模型列表
        """
        try:
            self.log_info("获取模型列表", strategy=strategy, limit=limit)
            
            models = list_models(strategy=strategy, limit=limit)
            
            # 实验 ID 过滤
            if experiment_id:
                models = [
                    m for m in models
                    if m.get('experiment_id') == experiment_id
                ]
            
            # 解析 JSON 字段
            for model in models:
                if model.get('metrics'):
                    model['metrics'] = json.loads(model['metrics'])
                if model.get('tags'):
                    model['tags'] = json.loads(model['tags'])
            
            self.log_info(f"获取到 {len(models)} 个模型")
            return models
            
        except Exception as e:
            self.log_error("获取模型列表失败", e)
            raise InternalError("获取模型列表失败", e)
    
    def get(self, model_id: str) -> Dict:
        """
        获取模型详情
        
        Args:
            model_id: 模型 ID
        
        Returns:
            模型详情
        
        Raises:
            NotFoundError: 模型不存在
        """
        try:
            self.log_info("获取模型详情", model_id=model_id)
            
            models = list_models(limit=1000)
            model = next((m for m in models if m['id'] == model_id), None)
            
            if not model:
                raise NotFoundError(f"模型不存在：{model_id}", "MODEL")
            
            # 解析 JSON 字段
            if model.get('metrics'):
                model['metrics'] = json.loads(model['metrics'])
            if model.get('tags'):
                model['tags'] = json.loads(model['tags'])
            
            self.log_info(f"获取模型成功：{model_id}")
            return model
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("获取模型详情失败", e, model_id=model_id)
            raise InternalError("获取模型详情失败", e)
    
    def create(
        self,
        name: str,
        strategy: str,
        experiment_id: str,
        model_path: str,
        metrics: Dict = None,
        tags: List[str] = None
    ) -> Dict:
        """
        创建模型记录
        
        Args:
            name: 模型名称
            strategy: 策略名称
            experiment_id: 实验 ID
            model_path: 模型文件路径
            metrics: 性能指标
            tags: 标签
        
        Returns:
            创建的模型
        
        Raises:
            ValidationError: 参数验证失败
        """
        try:
            # 参数验证
            if not name:
                raise ValidationError("模型名称不能为空", "name")
            if not strategy:
                raise ValidationError("策略名称不能为空", "strategy")
            if not experiment_id:
                raise ValidationError("实验 ID 不能为空", "experiment_id")
            if not model_path:
                raise ValidationError("模型路径不能为空", "model_path")
            
            # 生成模型 ID
            model_id = f"model_{strategy}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 计算模型哈希
            model_hash = self._calculate_model_hash(model_path)
            
            # 获取模型大小
            model_size = self._get_model_size(model_path)
            
            self.log_info(
                "创建模型",
                model_id=model_id,
                name=name,
                strategy=strategy,
                model_size=model_size
            )
            
            # 版本号
            version = self._get_next_version(strategy)
            
            # 创建模型记录
            success = create_model(
                model_id=model_id,
                name=name,
                strategy=strategy,
                version=version,
                experiment_id=experiment_id,
                metrics=metrics or {},
                model_path=model_path,
                model_hash=model_hash,
                model_size_bytes=model_size,
                framework="PPO"
            )
            
            if not success:
                raise InternalError("创建模型记录失败")
            
            # 返回创建的模型
            models = list_models(strategy=strategy, limit=1)
            model = models[0] if models else None
            
            if model and model.get('metrics'):
                model['metrics'] = json.loads(model['metrics'])
            
            self.log_info(f"模型创建成功：{model_id}")
            return model
            
        except ValidationError:
            raise
        except Exception as e:
            self.log_error("创建模型失败", e, name=name)
            raise InternalError("创建模型失败", e)
    
    def update(self, model_id: str, **kwargs) -> Dict:
        """
        更新模型（暂不支持）
        
        模型是不可变的，更新需要创建新版本
        """
        raise InternalError("模型不可变，请创建新版本")
    
    def delete(self, model_id: str) -> bool:
        """
        删除模型文件（暂不支持）
        
        模型删除需要谨慎，建议保留历史版本
        """
        raise InternalError("模型删除暂不支持，建议保留历史版本")
    
    def get_best(self, strategy: str = None, limit: int = 10) -> List[Dict]:
        """
        获取最佳模型（按收益排序）
        
        Args:
            strategy: 策略过滤
            limit: 数量限制
        
        Returns:
            最佳模型列表
        """
        try:
            self.log_info("获取最佳模型", strategy=strategy, limit=limit)
            
            models = get_best_models(limit=limit)
            
            # 策略过滤
            if strategy:
                models = [
                    m for m in models
                    if m.get('strategy') == strategy
                ]
            
            # 解析 JSON 字段
            for model in models:
                if model.get('metrics'):
                    model['metrics'] = json.loads(model['metrics'])
            
            self.log_info(f"获取到 {len(models)} 个最佳模型")
            return models
            
        except Exception as e:
            self.log_error("获取最佳模型失败", e)
            raise InternalError("获取最佳模型失败", e)
    
    def _calculate_model_hash(self, model_path: str) -> str:
        """计算模型文件哈希"""
        try:
            path = Path(model_path)
            if not path.exists():
                return "unknown"
            
            hasher = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            
            return hasher.hexdigest()[:16]
            
        except Exception as e:
            self.log_error("计算模型哈希失败", e)
            return "unknown"
    
    def _get_model_size(self, model_path: str) -> int:
        """获取模型文件大小"""
        try:
            path = Path(model_path)
            if path.exists():
                return path.stat().st_size
            return 0
        except:
            return 0
    
    def _get_next_version(self, strategy: str) -> int:
        """获取下一个版本号"""
        try:
            models = list_models(strategy=strategy, limit=100)
            if not models:
                return 1
            
            max_version = max(m.get('version', 0) for m in models)
            return max_version + 1
            
        except:
            return 1
