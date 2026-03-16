"""
服务层基类
提供通用的服务方法和日志记录
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ServiceBase(ABC):
    """服务层基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.created_at = datetime.now()
    
    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"{message} {extra_info}".strip())
    
    def log_error(self, message: str, error: Exception = None, **kwargs):
        """记录错误日志"""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        error_msg = f"{message} {extra_info}".strip()
        if error:
            error_msg += f" - {str(error)}"
        self.logger.error(error_msg, exc_info=True)
    
    def log_debug(self, message: str, **kwargs):
        """记录调试日志"""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.debug(f"{message} {extra_info}".strip())
    
    @abstractmethod
    def list(self, **kwargs) -> List[Dict]:
        """获取列表（抽象方法）"""
        pass
    
    @abstractmethod
    def get(self, id: str) -> Dict:
        """获取单个资源（抽象方法）"""
        pass
    
    @abstractmethod
    def create(self, data: Dict) -> Dict:
        """创建资源（抽象方法）"""
        pass
    
    @abstractmethod
    def update(self, id: str, data: Dict) -> Dict:
        """更新资源（抽象方法）"""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """删除资源（抽象方法）"""
        pass
