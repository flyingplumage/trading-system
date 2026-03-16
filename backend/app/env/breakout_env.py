"""
突破策略交易环境

策略逻辑：
- 突破关键价位时买入
- 跌破支撑位时卖出
- 使用 Donchian Channel、ATR 等指标
"""

import numpy as np
import pandas as pd
from typing import Optional

from .base import TradingEnvBase


class BreakoutEnv(TradingEnvBase):
    """突破策略环境"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        initial_cash: float = 1000000.0,
        commission_rate: float = 0.0003,
        slippage: float = 0.001,
        window_size: int = 20,
        breakout_window: int = 20,
        atr_window: int = 14,
        render_mode: Optional[str] = None
    ):
        """
        初始化突破环境
        
        Args:
            breakout_window: 突破检测窗口
            atr_window: ATR 计算窗口
        """
        super().__init__(
            df=df,
            initial_cash=initial_cash,
            commission_rate=commission_rate,
            slippage=slippage,
            window_size=window_size,
            render_mode=render_mode
        )
        
        self.breakout_window = breakout_window
        self.atr_window = atr_window
        
        # 观察空间
        from gymnasium import spaces
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(5 + 3,),  # 5 个特征 + 3 个账户信息
            dtype=np.float32
        )
    
    def _calculate_features(self, window_data: pd.DataFrame) -> np.ndarray:
        """
        计算突破特征
        
        特征包括：
        1. 价格相对于 N 日高点的位置
        2. 价格相对于 N 日低点的位置
        3. ATR（波动率）
        4. 价格突破强度
        5. 成交量突破
        """
        features = []
        
        if len(window_data) < self.breakout_window:
            return np.zeros(5)
        
        close = window_data['close'].values
        high = window_data['high'].values if 'high' in window_data.columns else close
        low = window_data['low'].values if 'low' in window_data.columns else close
        volume = window_data['vol'].values if 'vol' in window_data.columns else np.ones(len(close))
        
        current_price = close[-1]
        
        # 1. 价格相对于 N 日高点的位置
        n_high = np.max(high[-self.breakout_window:])
        high_position = (current_price - n_high) / n_high
        features.append(high_position)
        
        # 2. 价格相对于 N 日低点的位置
        n_low = np.min(low[-self.breakout_window:])
        low_position = (current_price - n_low) / n_low
        features.append(low_position)
        
        # 3. ATR (Average True Range)
        if len(high) >= self.atr_window + 1:
            true_ranges = []
            for i in range(1, min(self.atr_window + 1, len(high))):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                true_ranges.append(tr)
            atr = np.mean(true_ranges)
        else:
            atr = np.std(close)
        
        # 归一化 ATR
        atr_normalized = atr / current_price
        features.append(atr_normalized)
        
        # 4. 价格突破强度（距离高点的百分比）
        if n_high > 0:
            breakout_strength = (current_price - n_high) / n_high
        else:
            breakout_strength = 0
        features.append(breakout_strength)
        
        # 5. 成交量突破
        vol_ma = np.mean(volume[-self.breakout_window:])
        if vol_ma > 0:
            vol_breakout = (volume[-1] - vol_ma) / vol_ma
        else:
            vol_breakout = 0
        features.append(vol_breakout)
        
        return np.array(features)
    
    def _calculate_reward(self, action: int, current_price: float) -> float:
        """
        突破策略奖励函数
        
        奖励逻辑：
        - 突破高点时买入给予正奖励
        - 跌破低点时卖出给予正奖励
        - 假突破惩罚
        """
        reward = 0.0
        
        # 获取当前高低点
        if self.current_step >= self.breakout_window:
            window_high = self.df.iloc[self.current_step - self.breakout_window:self.current_step]['high'].max()
            window_low = self.df.iloc[self.current_step - self.breakout_window:self.current_step]['low'].min()
        else:
            window_high = current_price * 1.05
            window_low = current_price * 0.95
        
        # 突破判断
        breakout_up = current_price > window_high
        breakout_down = current_price < window_low
        
        # 突破交易奖励
        if breakout_up and action == 1:  # 向上突破买入
            reward += 0.2
        elif breakout_down and action == 2:  # 向下突破卖出
            reward += 0.2
        elif breakout_up and action == 2:  # 向上突破卖出（可能错过）
            reward -= 0.05
        elif breakout_down and action == 1:  # 向下突破买入（可能接刀）
            reward -= 0.05
        
        # 持仓奖励：趋势延续
        if self.position > 0:
            # 持仓且继续上涨
            if current_price > window_high:
                reward += 0.1
            # 持仓但回落
            elif current_price < window_high * 0.98:
                reward -= 0.05
        
        # 假突破惩罚（突破后快速回落）
        if self.current_step > self.breakout_window + 1:
            prev_price = self.df.iloc[self.current_step - 1]['close']
            if prev_price > window_high and current_price < window_high:
                reward -= 0.1  # 假突破
        
        # 交易惩罚
        if action in [1, 2]:
            reward -= self.commission_rate * 3
        
        return reward
