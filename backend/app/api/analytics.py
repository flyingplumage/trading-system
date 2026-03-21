"""
实验分析 API - 使用 DuckDB 加速查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.schemas import Response

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/experiments/{exp_id}/metrics", response_model=Response)
async def get_experiment_metrics(
    exp_id: str,
    limit: int = Query(default=10000, ge=1, le=100000)
):
    """
    获取实验指标历史（优先使用 DuckDB）
    
    Args:
        exp_id: 实验 ID
        limit: 返回记录数限制
    """
    try:
        # 优先从 DuckDB 查询（性能更好）
        try:
            from app.db.duckdb_analytics import get_metrics as duckdb_get_metrics
            metrics = duckdb_get_metrics(exp_id, limit)
            source = "duckdb"
        except Exception:
            # DuckDB 不可用时，从 SQLite 查询
            from app.db.database import get_experiment
            exp = get_experiment(exp_id)
            if not exp:
                raise HTTPException(status_code=404, detail="实验不存在")
            
            metrics = exp.get('metrics', [])
            if isinstance(metrics, str):
                import json
                metrics = [json.loads(metrics)]
            source = "sqlite"
        
        return Response(
            success=True,
            message="OK",
            data={
                'metrics': metrics,
                'source': source
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/compare", response_model=Response)
async def compare_experiments(
    exp_ids: str = Query(..., description="实验 ID 列表，逗号分隔")
):
    """
    对比多个实验的关键指标
    
    Args:
        exp_ids: 实验 ID 列表，如 "exp1,exp2,exp3"
    """
    try:
        exp_id_list = [x.strip() for x in exp_ids.split(',')]
        
        # 使用 DuckDB 对比
        try:
            from app.db.duckdb_analytics import compare_experiments as duckdb_compare
            result = duckdb_compare(exp_id_list)
            source = "duckdb"
        except Exception:
            # DuckDB 不可用时，返回基础信息
            from app.db.database import get_experiment
            result = []
            for exp_id in exp_id_list:
                exp = get_experiment(exp_id)
                if exp:
                    result.append({
                        'experiment_id': exp_id,
                        'name': exp.get('name'),
                        'strategy': exp.get('strategy'),
                        'status': exp.get('status')
                    })
            source = "sqlite"
        
        return Response(
            success=True,
            message="OK",
            data={
                'comparison': result,
                'source': source
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{exp_id}/stats", response_model=Response)
async def get_experiment_stats(exp_id: str):
    """
    获取实验统计摘要
    
    Args:
        exp_id: 实验 ID
    """
    try:
        # 从 DuckDB 获取统计
        try:
            from app.db.duckdb_analytics import get_metrics_summary
            stats = get_metrics_summary([exp_id])
            if stats:
                return Response(
                    success=True,
                    message="OK",
                    data=stats[0]
                )
        except Exception:
            pass
        
        # 降级：从 SQLite 获取
        from app.db.database import get_experiment
        exp = get_experiment(exp_id)
        if not exp:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        return Response(
            success=True,
            message="OK",
            data={
                'experiment_id': exp_id,
                'name': exp.get('name'),
                'status': exp.get('status'),
                'config': exp.get('config'),
                'metrics': exp.get('metrics')
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/stats", response_model=Response)
async def get_database_stats():
    """
    获取数据库统计信息
    """
    try:
        stats = {}
        
        # SQLite 统计
        try:
            from app.db.database import get_db_stats
            stats['sqlite'] = get_db_stats()
        except Exception as e:
            stats['sqlite'] = {'error': str(e)}
        
        # DuckDB 统计
        try:
            from app.db.duckdb_analytics import get_table_stats, get_database_size
            stats['duckdb'] = {
                'tables': get_table_stats(),
                'size_mb': get_database_size()
            }
        except Exception as e:
            stats['duckdb'] = {'error': str(e)}
        
        return Response(
            success=True,
            message="OK",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/cleanup", response_model=Response)
async def cleanup_database(
    days: int = Query(default=30, ge=1, le=365),
    dry_run: bool = Query(default=True)
):
    """
    清理旧的指标数据
    
    Args:
        days: 保留最近 N 天的数据
        dry_run: 是否仅预览（不实际删除）
    """
    try:
        # DuckDB 清理
        try:
            from app.db.duckdb_analytics import cleanup_old_metrics
            if dry_run:
                # 预览将删除的数据量
                from app.db.duckdb_analytics import get_connection
                from datetime import timedelta
                from datetime import datetime
                
                conn = get_connection()
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                result = conn.execute('''
                    SELECT COUNT(*) FROM experiment_metrics
                    WHERE created_at < ?
                ''', [cutoff_date]).fetchone()
                conn.close()
                
                return Response(
                    success=True,
                    message=f"预览：将删除 {result[0]} 条 {days} 天前的数据",
                    data={'will_delete': result[0]}
                )
            else:
                deleted = cleanup_old_metrics(days)
                return Response(
                    success=True,
                    message=f"已清理 {deleted} 条旧数据",
                    data={'deleted': deleted}
                )
        except Exception as e:
            return Response(
                success=False,
                message=f"DuckDB 清理失败：{e}",
                data={}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
