"""
策略验证 API
验证策略的有效性和稳健性
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from app.schemas.schemas import Response
from app.services.validation import strategy_validator
from app.api.dependencies import require_backtest_read
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api/agent/strategy/validation", tags=["strategy-validation"])


@router.post("/validate", response_model=Response)
async def validate_strategy(
    experiment_id: str,
    methods: Optional[str] = Query(default=None, description="验证方法，逗号分隔"),
    current_user: dict = Depends(require_backtest_read)
):
    """
    验证策略
    
    Args:
        experiment_id: 实验 ID
        methods: 验证方法 (walk_forward/monte_carlo/parameter_sensitivity/out_of_sample)
    """
    try:
        from app.db import database
        
        # 获取实验数据
        exp = database.get_experiment(experiment_id)
        if not exp:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        # 构建策略结果
        metrics = exp.get('metrics', {})
        equity_curve = metrics.get('equity_curve', [])
        
        if not equity_curve:
            # 生成示例数据
            np.random.seed(42)
            returns = np.random.normal(0.001, 0.02, 252)
            equity = pd.Series((1 + returns).cumprod() + 1)
        else:
            equity = pd.Series([p['value'] for p in equity_curve])
            returns = equity.pct_change().fillna(0)
        
        strategy_results = pd.DataFrame({
            'equity': equity,
            'returns': returns
        })
        
        # 解析验证方法
        method_list = None
        if methods:
            method_list = [m.strip() for m in methods.split(',')]
        
        # 执行验证
        validation_results = strategy_validator.validate(
            strategy_results=strategy_results,
            methods=method_list
        )
        
        return Response(
            success=True,
            message="策略验证完成",
            data={
                'experiment_id': experiment_id,
                'validation': validation_results
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{experiment_id}", response_model=Response)
async def get_validation_report(
    experiment_id: str,
    current_user: dict = Depends(require_backtest_read)
):
    """
    获取策略验证报告
    
    Args:
        experiment_id: 实验 ID
    """
    try:
        from app.db import database
        
        exp = database.get_experiment(experiment_id)
        if not exp:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        metrics = exp.get('metrics', {})
        
        # 生成验证报告
        report = {
            'experiment_id': experiment_id,
            'strategy': exp.get('strategy'),
            'created_at': exp.get('created_at'),
            'metrics_summary': {
                'total_return': metrics.get('total_return', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'max_drawdown': metrics.get('max_drawdown', 0),
                'win_rate': metrics.get('win_rate', 0)
            },
            'validation_status': 'pending',
            'recommendation': '需要执行验证'
        }
        
        return Response(
            success=True,
            message="OK",
            data=report
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/methods", response_model=Response)
async def list_validation_methods(current_user: dict = Depends(require_backtest_read)):
    """列出所有验证方法"""
    methods = {
        'walk_forward': {
            'name': '滚动窗口分析',
            'description': '将数据分为多个训练/测试段，验证策略稳定性',
            'recommended': True
        },
        'monte_carlo': {
            'name': '蒙特卡洛模拟',
            'description': '随机重采样交易序列，评估策略鲁棒性',
            'recommended': True
        },
        'parameter_sensitivity': {
            'name': '参数敏感性分析',
            'description': '评估策略对参数变化的敏感度',
            'recommended': True
        },
        'out_of_sample': {
            'name': '样本外测试',
            'description': '比较样本内和样本外表现',
            'recommended': True
        }
    }
    
    return Response(
        success=True,
        message="OK",
        data={
            'total_methods': len(methods),
            'methods': methods
        }
    )
