"""
智能体回测 API
提供回测结果、绩效指标、交易记录等数据
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Dict
from app.db import database
from app.schemas.schemas import Response
from app.services.backtest import backtest_service
from app.api.dependencies import require_backtest_read, require_backtest_create
import json
import uuid
from datetime import datetime

router = APIRouter(prefix="/backtest", tags=["Agent-Backtest"])

# 回测任务存储
backtest_tasks = {}

@router.post("/execute", response_model=Response)
async def execute_backtest(
    model_id: str,
    stock_code: str = '000001.SZ',
    start_date: str = None,
    end_date: str = None,
    initial_cash: float = 1000000.0,
    env_name: str = 'momentum',
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(require_backtest_create)
):
    """
    执行回测任务
    
    Args:
        model_id: 模型 ID
        stock_code: 股票代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        initial_cash: 初始资金
        env_name: 环境名称
    """
    
    # 创建回测任务 ID
    task_id = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # 记录任务
    backtest_tasks[task_id] = {
        'status': 'running',
        'model_id': model_id,
        'stock_code': stock_code,
        'created_at': datetime.now().isoformat()
    }
    
    def run_backtest():
        try:
            result = backtest_service.run_backtest(
                model_id=model_id,
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                env_name=env_name
            )
            backtest_tasks[task_id] = {
                'status': 'completed',
                'result': result
            }
            
            # 保存到数据库
            database.create_experiment(
                exp_id=task_id,
                name=f"backtest_{model_id}",
                strategy=f"backtest_{model_id}",
                config={
                    'model_id': model_id,
                    'stock_code': stock_code,
                    'env_name': env_name,
                    **result
                }
            )
            
            # 更新实验指标
            database.update_experiment(task_id, metrics=json.dumps(result))
            
        except Exception as e:
            backtest_tasks[task_id] = {
                'status': 'failed',
                'error': str(e)
            }
    
    if background_tasks:
        background_tasks.add_task(run_backtest)
    else:
        run_backtest()
    
    return Response(
        success=True,
        message="回测已启动",
        data={
            'task_id': task_id,
            'status': 'running'
        }
    )

@router.get("/task/{task_id}", response_model=Response)
async def get_backtest_task(task_id: str, current_user: dict = Depends(require_backtest_read)):
    """获取回测任务状态"""
    task = backtest_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return Response(
        success=True,
        message="OK",
        data=task
    )

@router.get("/results", response_model=Response)
async def get_backtest_results(strategy: str = None, limit: int = 50, current_user: dict = Depends(require_backtest_read)):
    """获取回测结果列表"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        
        if strategy:
            cursor.execute("""
                SELECT id, strategy, metrics, created_at
                FROM experiments
                WHERE strategy = ? AND status = 'completed'
                ORDER BY created_at DESC
                LIMIT ?
            """, [strategy, limit])
        else:
            cursor.execute("""
                SELECT id, strategy, metrics, created_at
                FROM experiments
                WHERE status = 'completed'
                ORDER BY created_at DESC
                LIMIT ?
            """, [limit])
        
        results = [
            {
                'experiment_id': row[0],
                'strategy': row[1],
                'metrics': json.loads(row[2]) if row[2] else {},
                'created_at': row[3]
            }
            for row in cursor.fetchall()
        ]
    
    return Response(success=True, message="OK", data=results)

@router.get("/{experiment_id}/metrics", response_model=Response)
async def get_backtest_metrics(experiment_id: str, current_user: dict = Depends(require_backtest_read)):
    """获取回测绩效指标"""
    exp = database.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    metrics = exp.get('metrics', {})
    
    # 计算额外指标
    total_return = metrics.get('total_return', 0)
    sharpe = metrics.get('sharpe_ratio', 0)
    max_dd = metrics.get('max_drawdown', 0)
    win_rate = metrics.get('win_rate', 0)
    
    # 评分
    score = (
        total_return * 100 +
        sharpe * 10 +
        (1 - max_dd) * 50 +
        win_rate * 50
    ) / 4
    
    return Response(
        success=True,
        message="OK",
        data={
            'experiment_id': experiment_id,
            'metrics': metrics,
            'score': score,
            'rating': 'A' if score > 80 else 'B' if score > 60 else 'C'
        }
    )

@router.get("/{experiment_id}/trades", response_model=Response)
async def get_backtest_trades(experiment_id: str, current_user: dict = Depends(require_backtest_read)):
    """获取交易记录"""
    exp = database.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    # 从结果中获取交易记录
    metrics = exp.get('metrics', {})
    trades = metrics.get('trades', [])
    
    return Response(
        success=True,
        message="OK",
        data={
            'experiment_id': experiment_id,
            'trades': trades,
            'total_trades': len(trades)
        }
    )

@router.get("/{experiment_id}/equity", response_model=Response)
async def get_equity_curve(experiment_id: str, current_user: dict = Depends(require_backtest_read)):
    """获取资金曲线"""
    exp = database.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    metrics = exp.get('metrics', {})
    equity_curve = metrics.get('equity_curve', [])
    
    return Response(
        success=True,
        message="OK",
        data={
            'experiment_id': experiment_id,
            'equity_curve': equity_curve,
            'initial_cash': metrics.get('initial_cash', 1000000),
            'final_value': metrics.get('final_value', 0)
        }
    )

@router.post("/compare", response_model=Response)
async def compare_strategies(experiment_ids: List[str], current_user: dict = Depends(require_backtest_read)):
    """对比多个策略回测结果"""
    results = []
    
    for exp_id in experiment_ids:
        exp = database.get_experiment(exp_id)
        if exp:
            metrics = exp.get('metrics', {})
            results.append({
                'experiment_id': exp_id,
                'strategy': exp.get('strategy'),
                'metrics': metrics
            })
    
    # 计算排名
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

@router.post("/evaluate", response_model=Response)
async def evaluate_model(
    model_id: str,
    stock_codes: List[str] = None,
    env_names: List[str] = None,
    initial_cash: float = 1000000.0,
    current_user: dict = Depends(require_backtest_create)
):
    """
    批量评估模型
    
    Args:
        model_id: 模型 ID
        stock_codes: 股票代码列表 (默认 ['000001.SZ'])
        env_names: 环境名称列表 (默认 ['momentum'])
        initial_cash: 初始资金
    """
    if not stock_codes:
        stock_codes = ['000001.SZ']
    if not env_names:
        env_names = ['momentum']
    
    results = []
    
    for stock_code in stock_codes:
        for env_name in env_names:
            try:
                result = backtest_service.run_backtest(
                    model_id=model_id,
                    stock_code=stock_code,
                    initial_cash=initial_cash,
                    env_name=env_name
                )
                results.append({
                    'stock_code': stock_code,
                    'env_name': env_name,
                    'success': True,
                    'metrics': result
                })
            except Exception as e:
                results.append({
                    'stock_code': stock_code,
                    'env_name': env_name,
                    'success': False,
                    'error': str(e)
                })
    
    # 综合评分
    successful = [r for r in results if r['success']]
    if successful:
        avg_return = sum(r['metrics']['total_return'] for r in successful) / len(successful)
        avg_sharpe = sum(r['metrics']['sharpe_ratio'] for r in successful) / len(successful)
        composite_score = avg_return * 100 + avg_sharpe * 10
    else:
        composite_score = 0
    
    return Response(
        success=True,
        message="模型评估完成",
        data={
            'model_id': model_id,
            'total_tests': len(results),
            'successful': len(successful),
            'failed': len(results) - len(successful),
            'composite_score': composite_score,
            'details': results
        }
    )

@router.get("/models/{model_id}/summary", response_model=Response)
async def get_model_summary(model_id: str, current_user: dict = Depends(require_backtest_read)):
    """获取模型历史表现摘要"""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 查询包含该模型的所有实验
        cursor.execute("""
            SELECT id, strategy, metrics, created_at
            FROM experiments
            WHERE config LIKE ?
            ORDER BY created_at DESC
            LIMIT 20
        """, [f'%{model_id}%'])
        
        experiments = []
        for row in cursor.fetchall():
            metrics = json.loads(row[2]) if row[2] else {}
            experiments.append({
                'experiment_id': row[0],
                'strategy': row[1],
                'metrics': metrics,
                'created_at': row[3]
            })
    
    # 统计平均表现
    if experiments:
        metrics_list = [e['metrics'] for e in experiments if e['metrics']]
        avg_return = sum(m.get('total_return', 0) for m in metrics_list) / len(metrics_list) if metrics_list else 0
        avg_sharpe = sum(m.get('sharpe_ratio', 0) for m in metrics_list) / len(metrics_list) if metrics_list else 0
    else:
        avg_return = 0
        avg_sharpe = 0
    
    return Response(
        success=True,
        message="OK",
        data={
            'model_id': model_id,
            'total_experiments': len(experiments),
            'avg_return': avg_return,
            'avg_sharpe': avg_sharpe,
            'experiments': experiments
        }
    )
