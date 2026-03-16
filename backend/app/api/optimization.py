"""
参数推荐 API
基于优化算法的参数推荐
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, List
from app.schemas.schemas import Response
from app.services.optimization import parameter_optimizer
from app.api.dependencies import require_backtest_read, require_backtest_create

router = APIRouter(prefix="/api/agent/optimization/params", tags=["optimization"])


@router.post("/recommend", response_model=Response)
async def recommend_params(
    strategy: str = Body(...),
    n_trials: int = Body(default=20, ge=5, le=100),
    current_user: dict = Depends(require_backtest_create)
):
    """
    推荐最优参数
    
    Args:
        strategy: 策略名称 (momentum/mean_reversion/breakout)
        n_trials: 优化迭代次数
    """
    result = parameter_optimizer.recommend(
        strategy=strategy,
        n_trials=n_trials
    )
    
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return Response(
        success=True,
        message="参数推荐完成",
        data=result
    )


@router.post("/compare", response_model=Response)
async def compare_strategies(
    strategies: List[str] = Body(...),
    n_trials: int = Body(default=10, ge=5, le=50),
    current_user: dict = Depends(require_backtest_create)
):
    """
    比较多个策略的参数
    
    Args:
        strategies: 策略列表
        n_trials: 每个策略的优化迭代次数
    """
    result = parameter_optimizer.compare_strategies(
        strategies=strategies,
        n_trials=n_trials
    )
    
    return Response(
        success=True,
        message="策略对比完成",
        data=result
    )


@router.get("/spaces", response_model=Response)
async def get_param_spaces(current_user: dict = Depends(require_backtest_read)):
    """获取参数空间定义"""
    spaces = {}
    for strategy, params in parameter_optimizer.param_spaces.items():
        spaces[strategy] = {
            name: str(space) for name, space in params.items()
        }
    
    return Response(
        success=True,
        message="OK",
        data={
            'strategies': list(parameter_optimizer.param_spaces.keys()),
            'param_spaces': spaces
        }
    )


@router.get("/history/{strategy}", response_model=Response)
async def get_optimization_history(
    strategy: str,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_backtest_read)
):
    """
    获取参数优化历史
    
    Args:
        strategy: 策略名称
        limit: 返回数量
    """
    # 示例历史数据
    history = []
    for i in range(limit):
        history.append({
            'trial': i + 1,
            'params': {
                'lookback_period': 20 + i,
                'entry_threshold': 0.03 + i * 0.001
            },
            'score': 0.5 + i * 0.01,
            'timestamp': datetime.now().isoformat()
        })
    
    return Response(
        success=True,
        message="OK",
        data={
            'strategy': strategy,
            'history': history
        }
    )
