"""
检查点管理 - 支持断点续传
用于批量更新任务，防止中断后重头开始
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        """
        初始化检查点管理器
        
        Args:
            checkpoint_dir: 检查点目录
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, task_name: str, progress: Dict):
        """
        保存进度
        
        Args:
            task_name: 任务名称
            progress: 进度信息 {'last_index': 10, 'last_stock': '000001.SZ'}
        """
        checkpoint_file = self.checkpoint_dir / f"{task_name}.json"
        
        data = {
            'task_name': task_name,
            'updated_at': datetime.now().isoformat(),
            **progress
        }
        
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[Checkpoint] 保存进度：{task_name} - {progress}")
        except Exception as e:
            print(f"[Checkpoint] 保存失败：{e}")
    
    def load(self, task_name: str, max_age_hours: int = 24) -> Optional[Dict]:
        """
        加载进度
        
        Args:
            task_name: 任务名称
            max_age_hours: 检查点最大年龄（小时），超过则视为过期
        
        Returns:
            进度信息，如果不存在或过期则返回 None
        """
        checkpoint_file = self.checkpoint_dir / f"{task_name}.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否过期
            updated_at = datetime.fromisoformat(data['updated_at'])
            age_hours = (datetime.now() - updated_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                print(f"[Checkpoint] 检查点已过期 ({age_hours:.1f} 小时)，忽略")
                return None
            
            print(f"[Checkpoint] 加载进度：{task_name} - 索引 {data.get('last_index', 0)}")
            return data
        
        except Exception as e:
            print(f"[Checkpoint] 加载失败：{e}")
            return None
    
    def clear(self, task_name: str):
        """
        清除检查点
        
        Args:
            task_name: 任务名称
        """
        checkpoint_file = self.checkpoint_dir / f"{task_name}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            print(f"[Checkpoint] 清除检查点：{task_name}")
    
    def clear_all(self):
        """清除所有检查点"""
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            checkpoint_file.unlink()
        print(f"[Checkpoint] 清除所有检查点")
    
    def list_checkpoints(self) -> list:
        """
        列出所有检查点
        
        Returns:
            检查点列表
        """
        checkpoints = []
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                checkpoints.append({
                    'file': checkpoint_file.name,
                    'task_name': data.get('task_name', ''),
                    'updated_at': data.get('updated_at', ''),
                    'last_index': data.get('last_index', 0)
                })
            except:
                pass
        return checkpoints

# 全局实例
checkpoint_manager = CheckpointManager()
