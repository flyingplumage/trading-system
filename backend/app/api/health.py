"""
健康检查 API
- 系统健康状态
- 依赖服务检查
- 性能指标
"""

from fastapi import APIRouter, HTTPException
from app.schemas.schemas import Response
from app.db import get_db_stats
from pathlib import Path
import psutil
import time

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }


@router.get("/detailed")
async def detailed_health_check():
    """详细健康检查"""
    try:
        # 数据库检查
        db_stats = get_db_stats()
        
        # 磁盘检查
        disk = psutil.disk_usage('/')
        
        # 内存检查
        memory = psutil.virtual_memory()
        
        # 系统负载
        try:
            load_avg = psutil.getloadavg()
        except:
            load_avg = (0, 0, 0)
        
        health = {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": time.time(),
            "checks": {
                "database": {
                    "status": "healthy",
                    "stats": db_stats
                },
                "disk": {
                    "status": "healthy" if disk.percent < 90 else "warning",
                    "usage_percent": disk.percent,
                    "free_gb": disk.free / (1024 ** 3)
                },
                "memory": {
                    "status": "healthy" if memory.percent < 90 else "warning",
                    "usage_percent": memory.percent,
                    "available_gb": memory.available / (1024 ** 3)
                },
                "system": {
                    "load_avg": load_avg,
                    "cpu_count": psutil.cpu_count(),
                    "status": "healthy"
                }
            }
        }
        
        # 总体状态判断
        if disk.percent >= 95 or memory.percent >= 95:
            health["status"] = "unhealthy"
        elif disk.percent >= 90 or memory.percent >= 90:
            health["status"] = "warning"
        
        return health
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/ready")
async def readiness_check():
    """就绪检查（K8s readiness probe）"""
    try:
        # 检查数据库连接
        db_stats = get_db_stats()
        
        # 检查必要目录
        required_dirs = [
            Path(__file__).parent.parent / "shared" / "data",
            Path(__file__).parent.parent / "shared" / "models",
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                raise Exception(f"必要目录不存在：{dir_path}")
        
        return {
            "status": "ready",
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")


@router.get("/live")
async def liveness_check():
    """存活检查（K8s liveness probe）"""
    return {
        "status": "alive",
        "timestamp": time.time()
    }


@router.get("/metrics")
async def get_metrics():
    """获取性能指标"""
    try:
        # 系统指标
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 数据库指标
        db_stats = get_db_stats()
        
        metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024 ** 3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 ** 3)
            },
            "database": db_stats,
            "timestamp": time.time()
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
