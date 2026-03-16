"""
策略服务类
负责策略的上传、验证和管理
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import ServiceBase
from .exceptions import NotFoundError, ValidationError, InternalError


class StrategyService(ServiceBase):
    """策略服务类"""
    
    def __init__(self):
        super().__init__()
        self.strategies_dir = Path(__file__).parent.parent.parent / "shared" / "strategies"
        self.strategies_dir.mkdir(parents=True, exist_ok=True)
        self.log_info("StrategyService 初始化")
    
    def list(self, **kwargs) -> List[Dict]:
        """
        获取策略列表
        
        Returns:
            策略列表
        """
        try:
            self.log_info("获取策略列表")
            
            strategies = []
            
            # 扫描策略目录
            for strategy_file in self.strategies_dir.glob("*.py"):
                if strategy_file.is_file():
                    strategy_info = self._parse_strategy_info(strategy_file)
                    strategies.append(strategy_info)
            
            self.log_info(f"找到 {len(strategies)} 个策略")
            return strategies
            
        except Exception as e:
            self.log_error("获取策略列表失败", e)
            raise InternalError("获取策略列表失败", e)
    
    def get(self, strategy_name: str) -> Dict:
        """
        获取策略详情
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            策略详情
        
        Raises:
            NotFoundError: 策略不存在
        """
        try:
            self.log_info("获取策略详情", strategy_name=strategy_name)
            
            strategy_file = self.strategies_dir / f"{strategy_name}.py"
            
            if not strategy_file.exists():
                raise NotFoundError(f"策略不存在：{strategy_name}", "STRATEGY")
            
            strategy_info = self._parse_strategy_info(strategy_file)
            
            self.log_info(f"获取策略成功：{strategy_name}")
            return strategy_info
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("获取策略详情失败", e, strategy_name=strategy_name)
            raise InternalError("获取策略详情失败", e)
    
    def create(self, data: Dict) -> Dict:
        """
        创建策略（上传策略文件）
        
        Args:
            data: 策略数据 {name, code, description, config}
        
        Returns:
            创建的策略信息
        
        Raises:
            ValidationError: 参数验证失败
        """
        try:
            # 参数验证
            name = data.get('name')
            code = data.get('code')
            
            if not name:
                raise ValidationError("策略名称不能为空", "name")
            if not code:
                raise ValidationError("策略代码不能为空", "code")
            
            # 验证策略代码
            self._validate_strategy_code(code)
            
            # 生成策略文件名
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            strategy_name = f"{name}_{timestamp}"
            strategy_file = self.strategies_dir / f"{strategy_name}.py"
            
            self.log_info("创建策略", name=strategy_name)
            
            # 保存策略文件
            with open(strategy_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 计算哈希
            file_hash = self._calculate_file_hash(strategy_file)
            
            strategy_info = {
                'id': strategy_name,
                'name': strategy_name,
                'file_path': str(strategy_file),
                'file_hash': file_hash,
                'file_size': strategy_file.stat().st_size,
                'created_at': datetime.now().isoformat(),
                'status': 'active',
                'description': data.get('description', ''),
                'config': data.get('config', {})
            }
            
            self.log_info(f"策略创建成功：{strategy_name}")
            return strategy_info
            
        except ValidationError:
            raise
        except Exception as e:
            self.log_error("创建策略失败", e, name=name)
            raise InternalError("创建策略失败", e)
    
    def update(self, strategy_name: str, data: Dict) -> Dict:
        """
        更新策略（暂不支持）
        
        策略是不可变的，更新需要上传新版本
        """
        raise InternalError("策略不可变，请上传新版本")
    
    def delete(self, strategy_name: str) -> bool:
        """
        删除策略文件
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            是否成功
        
        Raises:
            NotFoundError: 策略不存在
        """
        try:
            self.log_info("删除策略", strategy_name=strategy_name)
            
            strategy_file = self.strategies_dir / f"{strategy_name}.py"
            
            if not strategy_file.exists():
                raise NotFoundError(f"策略不存在：{strategy_name}", "STRATEGY")
            
            # 删除文件
            strategy_file.unlink()
            
            self.log_info(f"策略删除成功：{strategy_name}")
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("删除策略失败", e, strategy_name=strategy_name)
            raise InternalError("删除策略失败", e)
    
    def _parse_strategy_info(self, strategy_file: Path) -> Dict:
        """解析策略文件信息"""
        try:
            stat = strategy_file.stat()
            
            # 尝试读取策略元数据
            description = ""
            config = {}
            
            with open(strategy_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 尝试解析 docstring
                if '"""' in content:
                    start = content.find('"""') + 3
                    end = content.find('"""', start)
                    if end > start:
                        description = content[start:end].strip()
                
                # 尝试解析 CONFIG 变量
                if 'CONFIG' in content:
                    import re
                    match = re.search(r'CONFIG\s*=\s*(\{[^}]+\})', content)
                    if match:
                        try:
                            config = eval(match.group(1))
                        except:
                            pass
            
            return {
                'id': strategy_file.stem,
                'name': strategy_file.stem,
                'file_path': str(strategy_file),
                'file_size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'description': description,
                'config': config,
                'status': 'active'
            }
            
        except Exception as e:
            self.log_error("解析策略信息失败", e)
            return {
                'id': strategy_file.stem,
                'name': strategy_file.stem,
                'file_path': str(strategy_file),
                'status': 'unknown'
            }
    
    def _validate_strategy_code(self, code: str):
        """验证策略代码语法"""
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            raise ValidationError(f"策略代码语法错误：{e}", "code")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]
        except:
            return "unknown"
