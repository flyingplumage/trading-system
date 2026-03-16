"""
智能体调优 API
提供参数优化、超参数搜索、性能对比等数据
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.db import database
from app.schemas.schemas import Response
import json
import numpy as np

router = APIRouter(prefix="/api/agent/optimization", tags=["Agent-Optimization"])

@router.get("/params/recommend", response_model=Response)
async def recommend_params(strategy: str, current_metrics: Dict = None):
    """推荐优化参数"""
    # 基于历史数据推荐参数
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT metrics
            FROM experiments
            WHERE strategy = ? AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT 10
        """, [strategy])
        
        historical = [json.loads(row[0]) for row in cursor.fetchall() if row[0]]
    
    # 简单推荐逻辑
    recommendations = {
        'learning_rate': {
            'current': 3e-5,
            'recommended': 2e-5 if historical and np.mean([h.get('sharpe_ratio', 0) for h in historical]) < 1.5 else 3e-5,
            'range': [1e-5, 5e-5]
        },
        'n_steps': {
            'current': 1024,
            'recommended': 2048,
            'range': [512, 2048]
        },
        'batch_size': {
            'current': 64,
            'recommended': 128,
            'range': [32, 256]
        }
    }
    
    return Response(
        success=True,
        message="OK",
        data={
            'strategy': strategy,
            'recommendations': recommendations,
            'historical_count': len(historical)
        }
    )

@router.post("/params/search", response_model=Response)
async def search_params(
    strategy: str,
    param_ranges: Dict[str, List],
    n_trials: int = 20
):
    """超参数搜索"""
    # 生成搜索空间
    search_space = {}
    for param, range_val in param_ranges.items():
        if len(range_val) == 2:
            search_space[param] = {
                'min': range_val[0],
                'max': range_val[1]
            }
    
    # 返回搜索配置
    return Response(
        success=True,
        message="超参数搜索已配置",
        data={
            'strategy': strategy,
            'search_space': search_space,
            'n_trials': n_trials,
            'status': 'ready'
        }
    )

@router.get("/results/{strategy}", response_model=Response)
async def get_optimization_results(strategy: str):
    """获取调优结果"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, strategy, metrics, config, created_at
            FROM experiments
            WHERE strategy = ? AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT 50
        """, [strategy])
        
        results = [
            {
                'experiment_id': row[0],
                'strategy': row[1],
                'metrics': json.loads(row[2]) if row[2] else {},
                'config': json.loads(row[3]) if row[3] else {},
                'created_at': row[4]
            }
            for row in cursor.fetchall()
        ]
    
    # 找出最优结果
    if results:
        best = max(results, key=lambda x: x['metrics'].get('total_return', 0))
    else:
        best = None
    
    return Response(
        success=True,
        message="OK",
        data={
            'strategy': strategy,
            'results': results,
            'best': best,
            'total_count': len(results)
        }
    )

@router.get("/improvement/{experiment_id}", response_model=Response)
async def calculate_improvement(experiment_id: str):
    """计算性能提升"""
    exp = database.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    strategy = exp.get('strategy')
    metrics = exp.get('metrics', {})
    
    # 获取基线 (第一个完成的实验)
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT metrics
            FROM experiments
            WHERE strategy = ? AND status = 'completed'
            ORDER BY created_at ASC
            LIMIT 1
        """, [strategy])
        
        baseline_row = cursor.fetchone()
        baseline = json.loads(baseline_row[0]) if baseline_row and baseline_row[0] else {}
    
    # 计算提升
    improvement = {
        'total_return': (metrics.get('total_return', 0) - baseline.get('total_return', 0)) / baseline.get('total_return', 1) if baseline.get('total_return', 0) != 0 else 0,
        'sharpe_ratio': metrics.get('sharpe_ratio', 0) - baseline.get('sharpe_ratio', 0),
        'max_drawdown': metrics.get('max_drawdown', 0) - baseline.get('max_drawdown', 0),
        'win_rate': metrics.get('win_rate', 0) - baseline.get('win_rate', 0)
    }
    
    return Response(
        success=True,
        message="OK",
        data={
            'experiment_id': experiment_id,
            'baseline': baseline,
            'current': metrics,
            'improvement': improvement
        }
    )
