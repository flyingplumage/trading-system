"""Pydantic 数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

# 实验相关
class ExperimentBase(BaseModel):
    name: str
    strategy: str
    config: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []

class ExperimentCreate(ExperimentBase):
    pass

class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class Experiment(ExperimentBase):
    id: str
    status: str
    metrics: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 模型相关
class ModelBase(BaseModel):
    name: str
    strategy: str
    tags: Optional[List[str]] = []

class ModelRegister(ModelBase):
    experiment_id: str
    metrics: Dict[str, Any]
    model_path: str
    model_hash: str
    version: Optional[int] = None

class Model(ModelBase):
    id: str
    version: int
    experiment_id: str
    metrics: Dict[str, Any]
    model_path: str
    model_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

# 训练任务相关
class TrainingTaskCreate(BaseModel):
    strategy: str
    steps: int = 100000
    priority: int = 5

class TrainingTask(BaseModel):
    id: int
    strategy: str
    steps: int
    status: str
    priority: int
    experiment_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 通用响应
class Response(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    success: bool
    total: int
    items: List[Any]
