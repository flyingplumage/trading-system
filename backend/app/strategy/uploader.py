"""
策略上传管理器
"""

import os
import json
import shutil
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class StrategyUploader:
    """策略上传管理器"""
    
    def __init__(self, upload_dir: str = None):
        if upload_dir is None:
            self.upload_dir = Path(__file__).parent.parent.parent / "strategies"
        else:
            self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def upload(self, file_path: str, strategy_name: str, description: str = "") -> Dict:
        """
        上传策略包
        
        Args:
            file_path: 上传的文件路径 (ZIP 格式)
            strategy_name: 策略名称
            description: 策略描述
            
        Returns:
            策略信息字典
        """
        # 生成策略 ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        strategy_id = f"{strategy_name}_{timestamp}"
        
        # 创建策略目录
        strategy_dir = self.upload_dir / strategy_id
        strategy_dir.mkdir(parents=True, exist_ok=True)
        
        # 解压策略包
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(strategy_dir)
        else:
            # 直接复制
            shutil.copy(file_path, strategy_dir)
        
        # 计算哈希
        model_hash = self._calculate_hash(strategy_dir)
        
        # 创建策略元数据
        metadata = {
            'strategy_id': strategy_id,
            'strategy_name': strategy_name,
            'description': description,
            'upload_time': datetime.now().isoformat(),
            'model_hash': model_hash,
            'files': self._list_files(strategy_dir)
        }
        
        # 保存元数据
        metadata_path = strategy_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # 验证策略包结构
        validation = self._validate_strategy(strategy_dir)
        metadata['validation'] = validation
        
        # 更新元数据
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    def _calculate_hash(self, directory: Path) -> str:
        """计算策略包哈希"""
        hasher = hashlib.sha256()
        for file in sorted(directory.rglob('*')):
            if file.is_file() and file.name != 'metadata.json':
                hasher.update(file.read_bytes())
        return hasher.hexdigest()[:16]
    
    def _list_files(self, directory: Path) -> list:
        """列出策略包文件"""
        files = []
        for file in directory.rglob('*'):
            if file.is_file() and file.name != 'metadata.json':
                rel_path = file.relative_to(directory)
                files.append(str(rel_path))
        return files
    
    def _validate_strategy(self, directory: Path) -> Dict:
        """验证策略包结构"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'required_files': [],
            'optional_files': []
        }
        
        # 必需文件
        required = ['config.json']
        for file in required:
            if (directory / file).exists():
                validation['required_files'].append(file)
            else:
                validation['errors'].append(f"缺少必需文件：{file}")
                validation['valid'] = False
        
        # 可选文件 (Pipeline 脚本)
        optional = ['train.py', 'backtest.py', 'optimize.py']
        for file in optional:
            if (directory / file).exists():
                validation['optional_files'].append(file)
        
        # 检查数据管道
        data_dir = directory / "data"
        if data_dir.exists():
            validation['warnings'].append("策略包含自定义数据目录")
        
        # 检查特征工程
        features_dir = directory / "features"
        if features_dir.exists():
            validation['warnings'].append("策略包含自定义特征工程")
        
        return validation
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        """获取策略信息"""
        strategy_dir = self.upload_dir / strategy_id
        metadata_path = strategy_dir / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path) as f:
                return json.load(f)
        return None
    
    def list_strategies(self) -> list:
        """列出所有策略"""
        strategies = []
        for strategy_dir in self.upload_dir.iterdir():
            if strategy_dir.is_dir():
                metadata_path = strategy_dir / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path) as f:
                        strategies.append(json.load(f))
        return strategies
