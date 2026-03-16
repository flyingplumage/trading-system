"""
均值回归策略交易环境

策略逻辑：
- 低买高卖
- 价格低于均值时买入，高于均值时卖出
- 使用布林带、RSI 等指标
"""

import numpy as np
import pandas as pd
from typing import Optional

from .base import TradingEnvBase


class MeanReversionEnv(TradingEnvBase):
    """均值回归策略环境"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        initial_cash: float = 1000000.0,
        commission_rate: float = 0.0003,
        slippage: float = 0.001,
        window_size: int = 20,
        bb_window: int = 20,
        bb_std: float = 2.0,
        render_mode: Optional[str] = None
    ):
        """
        初始化均值回归环境
        
        Args:
            bb_window: 布林带窗口
            bb_std: 布林带标准差倍数
        """
        super().__init__(
            df=df,
            initial_cash=initial_cash,
            commission_rate=commission_rate,
            slippage=slippage,
            window_size=window_size,
            render_mode=render_mode
        )
        
        self.bb_window = bb_window
        self.bb_std = bb_std
        
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
        计算均值回归特征
        
        特征包括：
        1. 价格相对于布林带下轨的位置
        2. 价格相对于布林带上轨的位置
        3. RSI
        4. 价格偏离均线的程度
        5. 布林带宽度
        """
        features = []
        
        if len(window_data) < self.bb_window:
            return np.zeros(5)
        
        close = window_data['close'].values
        
        # 计算布林带
        ma = np.mean(close[-self.bb_window:])
        std = np.std(close[-self.bb_window:])
        upper_band = ma + self.bb_std * std
        lower_band = ma - self.bb_std * std
        
        current_price = close[-1]
        
        # 1. 价格相对于下轨的位置（<0 表示低于下轨）
        lower_position = (current_price - lower_band) / lower_band
        features.append(lower_position)
        
        # 2. 价格相对于上轨的位置（>0 表示高于上轨）
        upper_position = (current_price - upper_band) / upper_band
        features.append(upper_position)
        
        # 3. RSI
        if len(close) > 1:
            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            
            avg_gain = np.mean(gain[-14:]) if len(gain) >= 14 else np.mean(gain)
            avg_loss = np.mean(loss[-14:]) if len(loss) >= 14 else np.mean(loss)
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 50
        
        features.append((rsi - 50) / 50)  # 归一化到 -1~1
        
        # 4. 价格偏离均线的程度
        deviation = (current_price - ma) / ma
        features.append(deviation)
        
        # 5. 布林带宽度（波动率）
        band_width = (upper_band - lower_band) / ma
        features.append(band_width)
        
        return np.array(features)
    
    def _calculate_reward(self, action: int, current_price: float) -> float:
        """
        均值回归策略奖励函数
        
        奖励逻辑：
        - 价格低于下轨时买入给予正奖励
        - 价格高于上轨时卖出给予正奖励
        - 追涨杀跌给予负奖励
        """
        reward = 0.0
        
        # 获取当前布林带
        if self.current_step >= self.bb_window:
            window_close = self.df.iloc[self.current_step - self.bb_window:self.current_step]['close'].values
            ma = np.mean(window_close)
            std = np.std(window_close)
            upper_band = ma + self.bb_std * std
            lower_band = ma - self.bb_std * std
        else:
            upper_band = current_price * 1.1
            lower_band = current_price * 0.9
            ma = current_price
        
        # 位置判断
        below_lower = current_price < lower_band
        above_upper = current_price > upper_band
        
        # 低买高卖奖励
        if below_lower and action == 1:  # 低于下轨买入
            reward += 0.2
        elif above_upper and action == 2:  # 高于上轨卖出
            reward += 0.2
        elif below_lower and action == 2:  # 低于下轨卖出（错误）
            reward -= 0.1
        elif above_upper and action == 1:  # 高于上轨买入（错误）
            reward -= 0.1
        
        # 持仓奖励：价格向均值回归
        if self.position > 0:
            if current_price > ma:  # 持仓且价格上涨
                reward += 0.05
            elif current_price < ma:  # 持仓但价格下跌
                reward -= 0.03
        
        # 交易惩罚
        if action in [1, 2]:
            reward -= self.commission_rate * 3
        
        return reward
