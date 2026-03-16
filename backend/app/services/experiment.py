"""
实验服务类
负责实验的 CRUD 操作和业务逻辑
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import ServiceBase
from .exceptions import NotFoundError, ValidationError, ConflictError, InternalError
from app.db import (
    create_experiment,
    get_experiment,
    list_experiments,
    update_experiment,
)


class ExperimentService(ServiceBase):
    """实验服务类"""
    
    def __init__(self):
        super().__init__()
        self.log_info("ExperimentService 初始化")
    
    def list(
        self,
        status: str = None,
        strategy: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        获取实验列表
        
        Args:
            status: 状态过滤
            strategy: 策略过滤
            limit: 数量限制
            offset: 偏移量
        
        Returns:
            实验列表
        """
        try:
            self.log_info("获取实验列表", status=status, strategy=strategy, limit=limit)
            
            experiments = list_experiments(status=status, limit=limit)
            
            # 策略过滤
            if strategy:
                experiments = [
                    exp for exp in experiments
                    if exp.get('strategy') == strategy
                ]
            
            # 解析 JSON 字段
            for exp in experiments:
                if exp.get('config'):
                    exp['config'] = json.loads(exp['config'])
                if exp.get('metrics'):
                    exp['metrics'] = json.loads(exp['metrics'])
                if exp.get('tags'):
                    exp['tags'] = json.loads(exp['tags'])
            
            # 分页
            if offset:
                experiments = experiments[offset:]
            
            self.log_info(f"获取到 {len(experiments)} 个实验")
            return experiments
            
        except Exception as e:
            self.log_error("获取实验列表失败", e)
            raise InternalError("获取实验列表失败", e)
    
    def get(self, exp_id: str) -> Dict:
        """
        获取实验详情
        
        Args:
            exp_id: 实验 ID
        
        Returns:
            实验详情
        
        Raises:
            NotFoundError: 实验不存在
        """
        try:
            self.log_info("获取实验详情", exp_id=exp_id)
            
            exp = get_experiment(exp_id)
            
            if not exp:
                raise NotFoundError(f"实验不存在：{exp_id}", "EXPERIMENT")
            
            # 解析 JSON 字段
            if exp.get('config'):
                exp['config'] = json.loads(exp['config'])
            if exp.get('metrics'):
                exp['metrics'] = json.loads(exp['metrics'])
            if exp.get('tags'):
                exp['tags'] = json.loads(exp['tags'])
            
            self.log_info(f"获取实验成功：{exp_id}")
            return exp
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("获取实验详情失败", e, exp_id=exp_id)
            raise InternalError("获取实验详情失败", e)
    
    def create(
        self,
        name: str,
        strategy: str,
        config: Dict,
        tags: List[str] = None
    ) -> Dict:
        """
        创建实验
        
        Args:
            name: 实验名称
            strategy: 策略名称
            config: 配置字典
            tags: 标签列表
        
        Returns:
            创建的实验
        
        Raises:
            ValidationError: 参数验证失败
            ConflictError: 实验已存在
        """
        try:
            # 参数验证
            if not name or not name.strip():
                raise ValidationError("实验名称不能为空", "name")
            if not strategy or not strategy.strip():
                raise ValidationError("策略名称不能为空", "strategy")
            
            # 生成实验 ID
            exp_id = f"exp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{name[:8]}"
            
            self.log_info("创建实验", exp_id=exp_id, name=name, strategy=strategy)
            
            # 检查是否已存在
            existing = get_experiment(exp_id)
            if existing:
                exp_id = f"{exp_id}_{datetime.now().microsecond}"
            
            # 创建实验
            success = create_experiment(
                exp_id=exp_id,
                name=name,
                strategy=strategy,
                config=config
            )
            
            if not success:
                raise InternalError("创建实验失败")
            
            # 返回创建的实验
            exp = get_experiment(exp_id)
            if exp:
                exp['config'] = json.loads(exp['config'])
            
            self.log_info(f"实验创建成功：{exp_id}")
            return exp
            
        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            self.log_error("创建实验失败", e, name=name)
            raise InternalError("创建实验失败", e)
    
    def update(
        self,
        exp_id: str,
        name: str = None,
        status: str = None,
        config: Dict = None,
        metrics: Dict = None,
        tags: List[str] = None
    ) -> Dict:
        """
        更新实验
        
        Args:
            exp_id: 实验 ID
            name: 新名称
            status: 新状态
            config: 新配置
            metrics: 新指标
            tags: 新标签
        
        Returns:
            更新后的实验
        
        Raises:
            NotFoundError: 实验不存在
        """
        try:
            self.log_info("更新实验", exp_id=exp_id)
            
            # 检查实验是否存在
            exp = get_experiment(exp_id)
            if not exp:
                raise NotFoundError(f"实验不存在：{exp_id}", "EXPERIMENT")
            
            # 构建更新数据
            update_data = {}
            if name:
                update_data['name'] = name
            if status:
                update_data['status'] = status
            if config:
                update_data['config'] = json.dumps(config)
            if metrics:
                update_data['metrics'] = json.dumps(metrics)
            if tags:
                update_data['tags'] = json.dumps(tags)
            
            if not update_data:
                self.log_debug("无更新内容", exp_id=exp_id)
                return exp
            
            # 执行更新
            success = update_experiment(exp_id, **update_data)
            
            if not success:
                raise InternalError("更新实验失败")
            
            # 返回更新后的实验
            updated_exp = get_experiment(exp_id)
            if updated_exp:
                if updated_exp.get('config'):
                    updated_exp['config'] = json.loads(updated_exp['config'])
                if updated_exp.get('metrics'):
                    updated_exp['metrics'] = json.loads(updated_exp['metrics'])
            
            self.log_info(f"实验更新成功：{exp_id}")
            return updated_exp
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("更新实验失败", e, exp_id=exp_id)
            raise InternalError("更新实验失败", e)
    
    def delete(self, exp_id: str) -> bool:
        """
        删除实验（软删除）
        
        Args:
            exp_id: 实验 ID
        
        Returns:
            是否成功
        
        Raises:
            NotFoundError: 实验不存在
        """
        try:
            self.log_info("删除实验", exp_id=exp_id)
            
            # 检查实验是否存在
            exp = get_experiment(exp_id)
            if not exp:
                raise NotFoundError(f"实验不存在：{exp_id}", "EXPERIMENT")
            
            # 软删除：更新状态为 deleted
            success = update_experiment(exp_id, status='deleted')
            
            if not success:
                raise InternalError("删除实验失败")
            
            self.log_info(f"实验删除成功：{exp_id}")
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("删除实验失败", e, exp_id=exp_id)
            raise InternalError("删除实验失败", e)
    
    def get_stats(self) -> Dict:
        """获取实验统计信息"""
        try:
            experiments = list_experiments(limit=1000)
            
            stats = {
                'total': len(experiments),
                'by_status': {},
                'by_strategy': {}
            }
            
            for exp in experiments:
                status = exp.get('status', 'unknown')
                strategy = exp.get('strategy', 'unknown')
                
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                stats['by_strategy'][strategy] = stats['by_strategy'].get(strategy, 0) + 1
            
            return stats
            
        except Exception as e:
            self.log_error("获取实验统计失败", e)
            raise InternalError("获取实验统计失败", e)
