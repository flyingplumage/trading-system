"""
回测服务
基于训练好的模型执行回测，生成绩效指标
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

# ML 库
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

# 本地环境
from app.env import get_env_class, list_envs
from app.db import database


class BacktestService:
    """回测服务类"""
    
    def __init__(self):
        self.model_dir = Path(__file__).parent.parent.parent / "shared" / "models"
        self.data_dir = Path(__file__).parent.parent.parent / "shared" / "data" / "features"
    
    def run_backtest(
        self,
        model_id: str,
        stock_code: str = '000001.SZ',
        start_date: str = None,
        end_date: str = None,
        initial_cash: float = 1000000.0,
        env_name: str = 'momentum'
    ) -> Dict:
        """
        执行回测
        
        Args:
            model_id: 模型 ID
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            initial_cash: 初始资金
            env_name: 环境名称
        
        Returns:
            回测结果字典
        """
        print(f"[Backtest] 开始回测 - 模型：{model_id}, 股票：{stock_code}")
        
        start_time = time.time()
        
        try:
            # 1. 加载模型
            model_path = self.model_dir / f"{model_id}.zip"
            if not model_path.exists():
                # 尝试其他命名格式
                model_files = list(self.model_dir.glob(f"*{model_id}*.zip"))
                if not model_files:
                    raise FileNotFoundError(f"模型文件不存在：{model_id}")
                model_path = model_files[0]
            
            print(f"[Backtest] 加载模型：{model_path}")
            model = PPO.load(str(model_path))
            
            # 2. 获取数据
            stock_file = self.data_dir / f"{stock_code.replace('.', '_')}.parquet"
            if not stock_file.exists():
                raise FileNotFoundError(f"股票数据不存在：{stock_code}")
            
            df = pd.read_parquet(stock_file)
            
            # 日期过滤
            if start_date:
                df = df[df['trade_date'] >= start_date]
            if end_date:
                df = df[df['trade_date'] <= end_date]
            
            if len(df) < 50:
                raise ValueError(f"数据量不足：{len(df)} 条")
            
            print(f"[Backtest] 获取到 {len(df)} 条数据")
            
            # 3. 创建环境
            EnvClass = get_env_class(env_name)
            
            def make_env():
                return EnvClass(
                    df=df,
                    initial_cash=initial_cash,
                    commission_rate=0.0003,
                    slippage=0.001,
                    window_size=20
                )
            
            env = DummyVecEnv([make_env])
            
            # 4. 执行回测
            print(f"[Backtest] 执行回测...")
            
            obs = env.reset()
            done = False
            trades = []
            portfolio_values = [initial_cash]
            rewards = []
            
            step = 0
            while not done:
                # 模型预测动作
                action, _states = model.predict(obs, deterministic=True)
                
                # 执行动作
                obs, reward, done, info = env.step(action)
                
                # 记录信息
                portfolio_values.append(info[0]['portfolio_value'])
                rewards.append(reward[0])
                
                if info[0].get('trade_executed'):
                    trades.append({
                        'step': step,
                        'type': 'buy' if info[0]['position'] > 0 else 'sell',
                        'price': info[0].get('trade_price', 0),
                        'shares': info[0].get('shares', 0),
                        'value': info[0].get('portfolio_value', 0),
                        'cash': info[0].get('cash', 0)
                    })
                
                step += 1
                
                # 安全限制
                if step > len(df):
                    break
            
            # 5. 计算绩效指标
            print(f"[Backtest] 计算绩效指标...")
            metrics = self._calculate_metrics(
                portfolio_values=portfolio_values,
                trades=trades,
                rewards=rewards,
                initial_cash=initial_cash
            )
            
            # 6. 生成资金曲线
            equity_curve = [
                {'step': i, 'value': v}
                for i, v in enumerate(portfolio_values)
            ]
            
            # 7. 保存回测结果
            result = {
                'model_id': model_id,
                'stock_code': stock_code,
                'env_name': env_name,
                'initial_cash': initial_cash,
                'final_value': metrics['final_value'],
                'total_return': metrics['total_return'],
                'annual_return': metrics['annual_return'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'max_drawdown': metrics['max_drawdown'],
                'win_rate': metrics['win_rate'],
                'total_trades': len(trades),
                'steps': step,
                'elapsed_seconds': time.time() - start_time,
                'trades': trades[-20:],  # 只保留最近 20 条交易
                'equity_curve': equity_curve[-100:],  # 只保留最近 100 个点
            }
            
            print(f"[Backtest] 回测完成 - 收益率：{metrics['total_return']*100:.2f}%, "
                  f"夏普比率：{metrics['sharpe_ratio']:.2f}")
            
            return result
            
        except Exception as e:
            print(f"[Backtest] 回测失败：{e}")
            raise
    
    def _calculate_metrics(
        self,
        portfolio_values: List[float],
        trades: List[Dict],
        rewards: List[float],
        initial_cash: float
    ) -> Dict:
        """计算绩效指标"""
        
        portfolio_values = np.array(portfolio_values)
        
        # 总收益率
        final_value = portfolio_values[-1]
        total_return = (final_value - initial_cash) / initial_cash
        
        # 年化收益率 (假设 252 个交易日)
        n_days = len(portfolio_values)
        if n_days > 1:
            annual_return = (1 + total_return) ** (252 / n_days) - 1
        else:
            annual_return = 0
        
        # 计算日收益率
        if len(portfolio_values) > 1:
            returns = np.diff(portfolio_values) / portfolio_values[:-1]
        else:
            returns = np.array([0])
        
        # 夏普比率 (假设无风险利率 3%)
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = (np.mean(returns) - 0.03/252) / np.std(returns) * np.sqrt(252)
        else:
            sharpe = 0
        
        # 最大回撤
        if len(portfolio_values) > 1:
            cum_returns = (1 + returns).cumprod()
            running_max = np.maximum.accumulate(cum_returns)
            drawdowns = cum_returns / running_max - 1
            max_drawdown = np.min(drawdowns)
        else:
            max_drawdown = 0
        
        # 胜率
        if len(trades) >= 2:
            # 计算每笔交易的盈亏
            winning_trades = 0
            for i in range(0, len(trades) - 1, 2):
                if i + 1 < len(trades):
                    buy_price = trades[i].get('price', 0)
                    sell_price = trades[i + 1].get('price', 0)
                    if buy_price > 0 and sell_price > buy_price:
                        winning_trades += 1
            
            total_round_trades = len(trades) // 2
            win_rate = winning_trades / total_round_trades if total_round_trades > 0 else 0
        else:
            win_rate = 0
        
        return {
            'final_value': float(final_value),
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'sharpe_ratio': float(sharpe),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'total_trades': len(trades),
        }


# 全局服务实例
backtest_service = BacktestService()
