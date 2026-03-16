"""
智能体策略 API
提供策略管理、对比、分析等数据
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.db import database
from app.strategy.uploader import StrategyUploader
from app.schemas.schemas import Response
import json

router = APIRouter(prefix="/api/agent/strategy", tags=["Agent-Strategy"])

uploader = StrategyUploader()

@router.get("/list", response_model=Response)
async def list_strategies():
    """获取所有策略"""
    strategies = uploader.list_strategies()
    return Response(success=True, message="OK", data=strategies)

@router.get("/{strategy_id}", response_model=Response)
async def get_strategy(strategy_id: str):
    """获取策略详情"""
    strategy = uploader.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    return Response(success=True, message="OK", data=strategy)

@router.get("/{strategy_id}/performance", response_model=Response)
async def get_strategy_performance(strategy_id: str):
    """获取策略性能数据"""
    strategy = uploader.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    strategy_name = strategy.get('strategy_name')
    
    # 获取该策略的所有实验
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT metrics, created_at
            FROM experiments
            WHERE strategy = ? AND status = 'completed'
            ORDER BY created_at DESC
        """, [strategy_name])
        
        experiments = [
            {
                'metrics': json.loads(row[0]) if row[0] else {},
                'created_at': row[1]
            }
            for row in cursor.fetchall()
        ]
    
    # 计算性能统计
    if experiments:
        metrics_list = [e['metrics'] for e in experiments]
        avg_return = sum(m.get('total_return', 0) for m in metrics_list) / len(metrics_list)
        avg_sharpe = sum(m.get('sharpe_ratio', 0) for m in metrics_list) / len(metrics_list)
        avg_dd = sum(m.get('max_drawdown', 0) for m in metrics_list) / len(metrics_list)
    else:
        avg_return = 0
        avg_sharpe = 0
        avg_dd = 0
    
    return Response(
        success=True,
        message="OK",
        data={
            'strategy_id': strategy_id,
            'strategy_name': strategy_name,
            'experiments_count': len(experiments),
            'avg_return': avg_return,
            'avg_sharpe': avg_sharpe,
            'avg_drawdown': avg_dd,
            'experiments': experiments
        }
    )

@router.post("/compare", response_model=Response)
async def compare_strategies(strategy_ids: List[str]):
    """对比多个策略"""
    results = []
    
    for strategy_id in strategy_ids:
        strategy = uploader.get_strategy(strategy_id)
        if strategy:
            strategy_name = strategy.get('strategy_name')
            
            # 获取性能数据
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT metrics
                    FROM experiments
                    WHERE strategy = ? AND status = 'completed'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, [strategy_name])
                
                row = cursor.fetchone()
                metrics = json.loads(row[0]) if row and row[0] else {}
            
            results.append({
                'strategy_id': strategy_id,
                'strategy_name': strategy_name,
                'metrics': metrics
            })
    
    # 排名
    results.sort(key=lambda x: x['metrics'].get('total_return', 0), reverse=True)
    for i, r in enumerate(results):
        r['rank'] = i + 1
    
    return Response(
        success=True,
        message="OK",
        data={
            'results': results,
            'best': results[0] if results else None
        }
    )

@router.get("/{strategy_id}/validation", response_model=Response)
async def validate_strategy(strategy_id: str):
    """验证策略包"""
    strategy = uploader.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    validation = strategy.get('validation', {})
    
    return Response(
        success=True,
        message="OK",
        data={
            'strategy_id': strategy_id,
            'valid': validation.get('valid', False),
            'errors': validation.get('errors', []),
            'warnings': validation.get('warnings', [])
        }
    )
