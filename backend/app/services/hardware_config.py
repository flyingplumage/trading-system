"""
硬件配置管理服务
管理训练任务的硬件资源分配和限制
"""

import os
import psutil
import torch
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime


class HardwareConfig:
    """硬件配置管理器"""
    
    def __init__(self, config_file: str = "backend/configs/hardware_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.system_info = self._get_system_info()
    
    def _get_system_info(self) -> Dict:
        """获取系统硬件信息"""
        info = {
            'cpu': {
                'count_physical': psutil.cpu_count(logical=False),
                'count_logical': psutil.cpu_count(logical=True),
                'freq_max': psutil.cpu_freq().max if psutil.cpu_freq() else 0,
                'freq_current': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            },
            'memory': {
                'total_gb': psutil.virtual_memory().total / (1024**3),
                'available_gb': psutil.virtual_memory().available / (1024**3),
                'percent_used': psutil.virtual_memory().percent
            },
            'gpu': {
                'available': torch.cuda.is_available(),
                'count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
                'devices': []
            },
            'disk': {
                'total_gb': psutil.disk_usage('/').total / (1024**3),
                'free_gb': psutil.disk_usage('/').free / (1024**3),
                'percent_used': psutil.disk_usage('/').percent
            }
        }
        
        # GPU 详细信息
        if info['gpu']['available']:
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                info['gpu']['devices'].append({
                    'id': i,
                    'name': props.name,
                    'memory_total_gb': props.total_memory / (1024**3),
                    'memory_allocated_gb': torch.cuda.memory_allocated(i) / (1024**3),
                    'memory_reserved_gb': torch.cuda.memory_reserved(i) / (1024**3),
                    'compute_capability': f"{props.major}.{props.minor}"
                })
        
        # Mac M1/M2 GPU
        if not info['gpu']['available'] and os.uname().sysname == 'Darwin':
            try:
                if torch.backends.mps.is_available():
                    info['gpu']['available'] = True
                    info['gpu']['count'] = 1
                    info['gpu']['devices'].append({
                        'id': 0,
                        'name': 'Apple Silicon GPU',
                        'type': 'mps',
                        'memory_total_gb': psutil.virtual_memory().total / (1024**3) * 0.5  # 估算
                    })
            except:
                pass
        
        return info
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            'cpu': {
                'max_cores': -1,  # -1 表示不限制
                'max_percent': 80,  # 最大 CPU 使用率百分比
                'affinity': []  # CPU 亲和性，空表示自动
            },
            'memory': {
                'max_gb': -1,  # -1 表示不限制
                'max_percent': 80,  # 最大内存使用率百分比
                'swap_allowed': False  # 是否允许使用 swap
            },
            'gpu': {
                'enabled': True,
                'device_ids': [],  # 空表示使用所有
                'memory_fraction': 0.8,  # 显存使用比例
                'allow_growth': True,  # 显存动态增长
                'mixed_precision': False  # 混合精度训练
            },
            'disk': {
                'max_use_percent': 90,  # 磁盘最大使用率
                'temp_dir': '/tmp/training',  # 临时目录
                'checkpoint_dir': './checkpoints'  # 检查点目录
            },
            'training': {
                'max_concurrent_tasks': 1,  # 最大并发训练任务
                'default_batch_size': 64,
                'default_learning_rate': 3e-5,
                'early_stopping': True,
                'patience': 10
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                # 合并配置
                for key, value in saved_config.items():
                    if key in default_config:
                        if isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
        
        return default_config
    
    def save_config(self):
        """保存配置到文件"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        return {
            'config': self.config,
            'system_info': self.system_info,
            'timestamp': datetime.now().isoformat()
        }
    
    def update_config(self, updates: Dict) -> Dict:
        """更新配置"""
        for key, value in updates.items():
            if key in self.config:
                if isinstance(value, dict) and isinstance(self.config[key], dict):
                    self.config[key].update(value)
                else:
                    self.config[key] = value
            else:
                self.config[key] = value
        
        self.save_config()
        return self.get_config()
    
    def apply_limits(self, task_id: str) -> Dict:
        """应用硬件限制"""
        applied = {}
        
        # CPU 限制
        cpu_config = self.config['cpu']
        if cpu_config['max_cores'] > 0:
            max_cores = min(cpu_config['max_cores'], self.system_info['cpu']['count_logical'])
            os.environ['OMP_NUM_THREADS'] = str(max_cores)
            os.environ['MKL_NUM_THREADS'] = str(max_cores)
            applied['cpu_cores'] = max_cores
        
        if cpu_config['max_percent'] > 0:
            # 使用 psutil 设置进程 CPU 限制 (需要额外处理)
            applied['cpu_max_percent'] = cpu_config['max_percent']
        
        # 内存限制
        memory_config = self.config['memory']
        if memory_config['max_gb'] > 0:
            import resource
            max_bytes = int(memory_config['max_gb'] * 1024**3)
            resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
            applied['memory_max_gb'] = memory_config['max_gb']
        
        # GPU 限制
        gpu_config = self.config['gpu']
        if gpu_config['enabled'] and self.system_info['gpu']['available']:
            device_ids = gpu_config['device_ids']
            if device_ids:
                os.environ['CUDA_VISIBLE_DEVICES'] = ','.join(map(str, device_ids))
                applied['gpu_devices'] = device_ids
            
            # 显存限制
            if gpu_config['allow_growth']:
                # PyTorch 显存动态增长
                torch.backends.cuda.matmul.allow_tf32 = True
                applied['gpu_allow_growth'] = True
            
            # 混合精度
            if gpu_config['mixed_precision']:
                applied['mixed_precision'] = True
        
        # 临时目录
        temp_dir = Path(self.config['disk']['temp_dir'])
        temp_dir.mkdir(parents=True, exist_ok=True)
        os.environ['TMPDIR'] = str(temp_dir)
        applied['temp_dir'] = str(temp_dir)
        
        return applied
    
    def check_resources(self) -> Dict:
        """检查当前资源状态"""
        current = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': (psutil.virtual_memory().total - psutil.virtual_memory().available) / (1024**3),
            'disk_percent': psutil.disk_usage('/').percent,
            'gpu': []
        }
        
        # GPU 状态
        if self.system_info['gpu']['available']:
            for i in range(torch.cuda.device_count()):
                current['gpu'].append({
                    'id': i,
                    'memory_used_gb': torch.cuda.memory_allocated(i) / (1024**3),
                    'memory_total_gb': torch.cuda.get_device_properties(i).total_memory / (1024**3),
                    'utilization': torch.cuda.utilization(i) if hasattr(torch.cuda, 'utilization') else 0
                })
        
        # 检查是否超出限制
        warnings = []
        if current['cpu_percent'] > self.config['cpu']['max_percent']:
            warnings.append(f"CPU 使用率过高：{current['cpu_percent']}% > {self.config['cpu']['max_percent']}%")
        
        if current['memory_percent'] > self.config['memory']['max_percent']:
            warnings.append(f"内存使用率过高：{current['memory_percent']}% > {self.config['memory']['max_percent']}%")
        
        if current['disk_percent'] > self.config['disk']['max_use_percent']:
            warnings.append(f"磁盘使用率过高：{current['disk_percent']}% > {self.config['disk']['max_use_percent']}%")
        
        return {
            'current': current,
            'warnings': warnings,
            'can_start_training': len(warnings) == 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_optimal_config(self, strategy: str = 'auto') -> Dict:
        """根据硬件情况推荐最优配置"""
        sys_info = self.system_info
        
        # CPU 核心数
        if sys_info['cpu']['count_logical'] >= 8:
            recommended_cores = 6
        elif sys_info['cpu']['count_logical'] >= 4:
            recommended_cores = 3
        else:
            recommended_cores = 2
        
        # 内存
        total_memory_gb = sys_info['memory']['total_gb']
        if total_memory_gb >= 32:
            recommended_memory = 24
        elif total_memory_gb >= 16:
            recommended_memory = 12
        else:
            recommended_memory = 8
        
        # GPU
        gpu_available = sys_info['gpu']['available']
        gpu_count = sys_info['gpu']['count']
        
        if gpu_available and gpu_count > 0:
            # 有 GPU
            batch_size = 128 if gpu_count >= 2 else 64
            use_gpu = True
        else:
            # 无 GPU
            batch_size = 32
            use_gpu = False
        
        return {
            'recommended': {
                'cpu_cores': recommended_cores,
                'memory_gb': recommended_memory,
                'use_gpu': use_gpu,
                'gpu_devices': list(range(gpu_count)) if gpu_available else [],
                'batch_size': batch_size,
                'learning_rate': 3e-5,
                'mixed_precision': gpu_available and gpu_count >= 2
            },
            'system_info': sys_info,
            'strategy': strategy
        }


# 全局硬件配置实例
hardware_config = HardwareConfig()
