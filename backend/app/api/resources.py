"""
资源监控 API
- 系统资源（CPU/内存/磁盘）
- GPU 状态
- 历史数据
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from app.schemas.schemas import Response
from pathlib import Path
import psutil
import subprocess
import json
from datetime import datetime
import torch

router = APIRouter(prefix="/api/resources", tags=["Resources"])

# 历史数据存储路径
HISTORY_DIR = Path(__file__).parent.parent.parent / "data" / "resource_history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def get_system_info() -> Dict:
    """获取系统资源信息"""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    
    # 内存
    memory = psutil.virtual_memory()
    
    # 磁盘
    disk = psutil.disk_usage('/')
    
    # 网络
    net = psutil.net_io_counters()
    
    return {
        'cpu': {
            'usage_percent': cpu_percent,
            'count': cpu_count,
            'frequency_mhz': cpu_freq.current if cpu_freq else 0,
            'per_cpu': psutil.cpu_percent(percpu=True)
        },
        'memory': {
            'total_gb': memory.total / (1024 ** 3),
            'available_gb': memory.available / (1024 ** 3),
            'used_gb': memory.used / (1024 ** 3),
            'usage_percent': memory.percent
        },
        'disk': {
            'total_gb': disk.total / (1024 ** 3),
            'used_gb': disk.used / (1024 ** 3),
            'free_gb': disk.free / (1024 ** 3),
            'usage_percent': disk.percent
        },
        'network': {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        },
        'timestamp': datetime.now().isoformat()
    }


def get_gpu_info() -> Dict:
    """获取 GPU 信息"""
    gpu_info = {
        'available': False,
        'count': 0,
        'gpus': [],
        'timestamp': datetime.now().isoformat()
    }
    
    # 检查 CUDA
    if torch.cuda.is_available():
        try:
            gpu_info['available'] = True
            gpu_info['count'] = torch.cuda.device_count()
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                
                # 获取显存使用
                memory_allocated = torch.cuda.memory_allocated(i)
                memory_reserved = torch.cuda.memory_reserved(i)
                memory_total = props.total_memory
                
                gpu_info['gpus'].append({
                    'id': i,
                    'name': props.name,
                    'memory_total_gb': memory_total / (1024 ** 3),
                    'memory_allocated_gb': memory_allocated / (1024 ** 3),
                    'memory_reserved_gb': memory_reserved / (1024 ** 3),
                    'memory_used_percent': (memory_allocated / memory_total) * 100,
                    'compute_capability': f"{props.major}.{props.minor}",
                    'multi_processor_count': props.multi_processor_count
                })
            
            # 获取 GPU 利用率（需要 nvidia-smi）
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
                     '--format=csv,nounits,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for idx, line in enumerate(lines):
                        if idx < len(gpu_info['gpus']):
                            parts = line.split(', ')
                            gpu_info['gpus'][idx]['utilization_percent'] = float(parts[0])
                            gpu_info['gpus'][idx]['memory_used_gb'] = float(parts[1]) / 1024
                            gpu_info['gpus'][idx]['memory_total_gb'] = float(parts[2]) / 1024
            except:
                pass
                
        except Exception as e:
            gpu_info['error'] = str(e)
    
    # 检查 Apple Silicon MPS
    elif torch.backends.mps.is_available():
        gpu_info['available'] = True
        gpu_info['count'] = 1
        gpu_info['gpus'].append({
            'id': 0,
            'name': 'Apple Silicon MPS',
            'memory_total_gb': psutil.virtual_memory().total / (1024 ** 3) * 0.5,  # 估算
            'memory_allocated_gb': 0,
            'memory_reserved_gb': 0,
            'memory_used_percent': 0,
            'type': 'MPS'
        })
    
    return gpu_info


def save_history(data: Dict, history_type: str):
    """保存历史数据"""
    timestamp = datetime.now().strftime('%Y%m%d')
    history_file = HISTORY_DIR / f"{history_type}_{timestamp}.jsonl"
    
    with open(history_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data) + '\n')


def get_history(history_type: str, limit: int = 100) -> List[Dict]:
    """获取历史数据"""
    timestamp = datetime.now().strftime('%Y%m%d')
    history_file = HISTORY_DIR / f"{history_type}_{timestamp}.jsonl"
    
    if not history_file.exists():
        return []
    
    history = []
    with open(history_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                history.append(json.loads(line))
            except:
                continue
    
    # 返回最新的 limit 条
    return history[-limit:]


@router.get("/system", response_model=Response)
async def get_system_resources():
    """获取系统资源状态（CPU/内存/磁盘）"""
    try:
        system_info = get_system_info()
        
        # 保存历史数据
        save_history(system_info, 'system')
        
        return Response(
            success=True,
            message="OK",
            data=system_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gpu", response_model=Response)
async def get_gpu_resources():
    """获取 GPU 状态"""
    try:
        gpu_info = get_gpu_info()
        
        # 保存历史数据
        if gpu_info['available']:
            save_history(gpu_info, 'gpu')
        
        return Response(
            success=True,
            message="OK",
            data=gpu_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=Response)
async def get_resource_history(
    type: str = "system",
    limit: int = 100
):
    """获取资源历史数据"""
    try:
        if type not in ['system', 'gpu']:
            raise HTTPException(status_code=400, detail="类型错误，应该是 'system' 或 'gpu'")
        
        history = get_history(type, limit)
        
        return Response(
            success=True,
            message="OK",
            data={
                'type': type,
                'count': len(history),
                'records': history
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=Response)
async def get_resource_summary():
    """获取资源摘要（快速检查）"""
    try:
        system = get_system_info()
        gpu = get_gpu_info()
        
        summary = {
            'cpu_usage': system['cpu']['usage_percent'],
            'memory_usage': system['memory']['usage_percent'],
            'memory_available_gb': system['memory']['available_gb'],
            'disk_usage': system['disk']['usage_percent'],
            'disk_free_gb': system['disk']['free_gb'],
            'gpu_available': gpu['available'],
            'gpu_count': gpu['count'],
            'gpu_name': gpu['gpus'][0]['name'] if gpu['gpus'] else None,
            'timestamp': datetime.now().isoformat()
        }
        
        return Response(
            success=True,
            message="OK",
            data=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
