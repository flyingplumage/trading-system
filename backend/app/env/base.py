"""
交易环境基类
基于 Gymnasium 框架
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import gymnasium as gym
from gymnasium import spaces


class TradingEnvBase(gym.Env, ABC):
    """
    交易环境基类
    
    子类需要实现：
    - _calculate_reward(): 奖励计算逻辑
    - _calculate_features(): 特征计算逻辑
    - action_space: 动作空间定义
    """
    
    metadata = {'render_modes': ['human']}
    
    def __init__(
        self,
        df: pd.DataFrame,
        initial_cash: float = 1000000.0,
        commission_rate: float = 0.0003,
        slippage: float = 0.001,
        window_size: int = 20,
        render_mode: Optional[str] = None
    ):
        """
        初始化交易环境
        
        Args:
            df: 股票数据（包含 OHLCV 等）
            initial_cash: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
            window_size: 观察窗口大小
            render_mode: 渲染模式
        """
        super().__init__()
        
        self.df = df.reset_index(drop=True)
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.window_size = window_size
        self.render_mode = render_mode
        
        # 数据验证
        assert len(self.df) > window_size, "数据量不足"
        
        # 状态变量
        self.current_step = None
        self.cash = None
        self.shares = None
        self.position = None  # -1 (空), 0 (观望), 1 (多)
        self.trades = None
        self.portfolio_values = None
        
        # 动作空间：0=持有/观望，1=买入，2=卖出
        self.action_space = spaces.Discrete(3)
        
        # 观察空间（由子类定义）
        self.observation_space = None
        
        print(f"[Env] 环境初始化完成，数据量：{len(self.df)}")
    
    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, dict]:
        """重置环境"""
        super().reset(seed=seed)
        
        # 初始化状态
        self.current_step = self.window_size
        self.cash = self.initial_cash
        self.shares = 0
        self.position = 0
        self.trades = []
        self.portfolio_values = [self.initial_cash]
        
        # 获取初始观察
        obs = self._get_observation()
        
        # 初始化信息
        info = {
            'step': 0,
            'cash': self.cash,
            'shares': self.shares,
            'portfolio_value': self.initial_cash,
            'position': self.position,
        }
        
        return obs, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        执行一步动作
        
        Args:
            action: 动作（0=持有，1=买入，2=卖出）
        
        Returns:
            observation, reward, terminated, truncated, info
        """
        # 获取当前价格
        current_price = self._get_current_price()
        
        # 执行动作
        info = self._execute_action(action, current_price)
        
        # 移动到下一步
        self.current_step += 1
        
        # 计算投资组合价值
        portfolio_value = self.cash + self.shares * current_price
        self.portfolio_values.append(portfolio_value)
        
        # 计算奖励
        reward = self._calculate_reward(action, current_price)
        
        # 检查是否结束
        terminated = self._check_termination()
        truncated = self.current_step >= len(self.df) - 1
        
        # 信息
        info = {
            'step': self.current_step - self.window_size,
            'total_steps': len(self.df) - self.window_size,
            'cash': self.cash,
            'shares': self.shares,
            'portfolio_value': portfolio_value,
            'position': self.position,
            'trade_executed': info.get('trade_executed', False),
            'trade_price': info.get('trade_price', 0),
            'trade_value': info.get('trade_value', 0),
        }
        
        # 获取新观察
        obs = self._get_observation()
        
        return obs, reward, terminated, truncated, info
    
    def _execute_action(self, action: int, price: float):
        """
        执行交易动作
        
        Args:
            action: 动作
            price: 当前价格
        """
        info = {'trade_executed': False}
        
        # 考虑滑点的价格
        if action == 1:  # 买入
            exec_price = price * (1 + self.slippage)
        elif action == 2:  # 卖出
            exec_price = price * (1 - self.slippage)
        else:
            exec_price = price
        
        if action == 1:  # 买入
            if self.position <= 0:  # 空仓或空位，可以买入
                # 全仓买入
                max_shares = int(self.cash / (exec_price * (1 + self.commission_rate)))
                if max_shares > 0:
                    cost = max_shares * exec_price * (1 + self.commission_rate)
                    self.cash -= cost
                    self.shares += max_shares
                    self.position = 1
                    
                    self.trades.append({
                        'step': self.current_step,
                        'type': 'buy',
                        'price': exec_price,
                        'shares': max_shares,
                        'value': cost
                    })
                    
                    info['trade_executed'] = True
                    info['trade_price'] = exec_price
                    info['trade_value'] = cost
        
        elif action == 2:  # 卖出
            if self.position > 0 and self.shares > 0:  # 有多头仓位
                # 全部卖出
                proceeds = self.shares * exec_price * (1 - self.commission_rate)
                self.cash += proceeds
                
                self.trades.append({
                    'step': self.current_step,
                    'type': 'sell',
                    'price': exec_price,
                    'shares': self.shares,
                    'value': proceeds
                })
                
                self.shares = 0
                self.position = 0
                
                info['trade_executed'] = True
                info['trade_price'] = exec_price
                info['trade_value'] = proceeds
        
        return info
    
    def _get_observation(self) -> np.ndarray:
        """获取当前观察"""
        # 获取窗口数据
        window_data = self.df.iloc[self.current_step - self.window_size:self.current_step]
        
        # 计算特征（由子类实现）
        features = self._calculate_features(window_data)
        
        # 添加账户信息
        account_info = np.array([
            self.cash / self.initial_cash,  # 现金比例
            self.shares * self._get_current_price() / self.initial_cash,  # 持仓价值比例
            self.position,  # 当前仓位
        ])
        
        # 合并特征
        obs = np.concatenate([features.flatten(), account_info])
        
        return obs
    
    @abstractmethod
    def _calculate_features(self, window_data: pd.DataFrame) -> np.ndarray:
        """
        计算特征（由子类实现）
        
        Args:
            window_data: 窗口期数据
        
        Returns:
            特征数组
        """
        pass
    
    @abstractmethod
    def _calculate_reward(self, action: int, current_price: float) -> float:
        """
        计算奖励（由子类实现）
        
        Args:
            action: 执行的动作
            current_price: 当前价格
        
        Returns:
            奖励值
        """
        pass
    
    def _get_current_price(self) -> float:
        """获取当前价格"""
        return self.df.iloc[self.current_step]['close']
    
    def _check_termination(self) -> bool:
        """检查是否应该终止"""
        # 破产检查
        if self.cash <= 0:
            return True
        
        # 投资组合价值低于阈值
        current_value = self.cash + self.shares * self._get_current_price()
        if current_value < self.initial_cash * 0.5:  # 亏损 50%
            return True
        
        return False
    
    def get_portfolio_values(self) -> List[float]:
        """获取投资组合价值历史"""
        return self.portfolio_values
    
    def get_trades(self) -> List[Dict]:
        """获取交易记录"""
        return self.trades
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取绩效指标"""
        if len(self.portfolio_values) < 2:
            return {}
        
        portfolio_values = np.array(self.portfolio_values)
        
        # 计算收益率
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        
        # 总收益率
        total_return = (portfolio_values[-1] - self.initial_cash) / self.initial_cash
        
        # 年化收益率（假设 252 个交易日）
        n_days = len(portfolio_values)
        annual_return = (1 + total_return) ** (252 / n_days) - 1
        
        # 夏普比率（假设无风险利率 3%）
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = (np.mean(returns) - 0.03/252) / np.std(returns) * np.sqrt(252)
        else:
            sharpe = 0
        
        # 最大回撤
        cum_returns = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cum_returns)
        drawdowns = cum_returns / running_max - 1
        max_drawdown = np.min(drawdowns)
        
        # 交易次数
        n_trades = len(self.trades)
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'n_trades': n_trades,
            'final_value': portfolio_values[-1],
        }
    
    def render(self):
        """渲染环境"""
        if self.render_mode == 'human':
            print(f"Step: {self.current_step}, "
                  f"Cash: {self.cash:.2f}, "
                  f"Shares: {self.shares}, "
                  f"Position: {self.position}")
