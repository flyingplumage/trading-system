"""
动量策略交易环境

策略逻辑：
- 追涨杀跌
- 价格上涨时买入，价格下跌时卖出
- 使用动量指标（ROC、RSI 等）
"""

import numpy as np
import pandas as pd
from typing import Optional

from .base import TradingEnvBase


class MomentumEnv(TradingEnvBase):
    """动量策略环境"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        initial_cash: float = 1000000.0,
        commission_rate: float = 0.0003,
        slippage: float = 0.001,
        window_size: int = 20,
        momentum_window: int = 10,
        render_mode: Optional[str] = None
    ):
        """
        初始化动量环境
        
        Args:
            momentum_window: 动量计算窗口
        """
        super().__init__(
            df=df,
            initial_cash=initial_cash,
            commission_rate=commission_rate,
            slippage=slippage,
            window_size=window_size,
            render_mode=render_mode
        )
        
        self.momentum_window = momentum_window
        
        # 观察空间：动量指标 + 价格特征 + 账户信息
        # 特征：ROC, RSI, 价格变化率，成交量变化，MA 比率
        n_features = 5  # 动量指标数量
        n_account = 3   # 账户信息
        from gymnasium import spaces
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(n_features + n_account,),
            dtype=np.float32
        )
    
    def _calculate_features(self, window_data: pd.DataFrame) -> np.ndarray:
        """
        计算动量特征
        
        特征包括：
        1. ROC (Rate of Change) - 价格变化率
        2. RSI (Relative Strength Index) - 相对强弱指标
        3. 价格相对于 MA 的位置
        4. 成交量变化率
        5. 价格动量（N 日涨幅）
        """
        features = []
        
        # 确保有足够数据
        if len(window_data) < self.momentum_window:
            return np.zeros(5)
        
        close = window_data['close'].values
        volume = window_data['vol'].values if 'vol' in window_data.columns else np.ones(len(close))
        
        # 1. ROC (10 日)
        roc = (close[-1] - close[-self.momentum_window]) / close[-self.momentum_window]
        features.append(roc)
        
        # 2. RSI (10 日)
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        if len(gain) >= self.momentum_window:
            avg_gain = np.mean(gain[-self.momentum_window:])
            avg_loss = np.mean(loss[-self.momentum_window:])
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 50
        
        features.append(rsi / 100)  # 归一化到 0-1
        
        # 3. 价格相对于 MA20 的位置
        ma20 = np.mean(close[-20:]) if len(close) >= 20 else close[-1]
        ma_ratio = (close[-1] - ma20) / ma20
        features.append(ma_ratio)
        
        # 4. 成交量变化率
        if len(volume) >= self.momentum_window:
            vol_ma = np.mean(volume[-self.momentum_window:])
            vol_change = (volume[-1] - vol_ma) / vol_ma
        else:
            vol_change = 0
        features.append(vol_change)
        
        # 5. 价格动量（5 日涨幅）
        if len(close) >= 5:
            momentum_5d = (close[-1] - close[-5]) / close[-5]
        else:
            momentum_5d = 0
        features.append(momentum_5d)
        
        return np.array(features)
    
    def _calculate_reward(self, action: int, current_price: float) -> float:
        """
        动量策略奖励函数
        
        奖励逻辑：
        - 持仓时价格上涨给予正奖励
        - 空仓时价格下跌给予正奖励（避免损失）
        - 错误操作给予负奖励（追高杀跌）
        - 交易手续费惩罚
        """
        reward = 0.0
        
        # 获取前一步价格
        if self.current_step > self.window_size:
            prev_price = self.df.iloc[self.current_step - 1]['close']
            price_change = (current_price - prev_price) / prev_price
        else:
            price_change = 0
            prev_price = current_price
        
        # 持仓奖励/惩罚
        if self.position > 0:  # 多头
            reward += price_change * 10  # 放大收益信号
        elif self.position < 0:  # 空头（暂不支持）
            reward -= price_change * 10
        
        # 交易惩罚（手续费）
        if action == 1 or action == 2:  # 买入或卖出
            reward -= self.commission_rate * 5  # 交易成本惩罚
        
        # 动量一致性奖励
        # 如果价格上涨且买入，或价格下跌且卖出，给予额外奖励
        if price_change > 0.01 and action == 1:  # 上涨时买入
            reward += 0.1
        elif price_change < -0.01 and action == 2:  # 下跌时卖出
            reward += 0.1
        elif price_change > 0.01 and action == 2:  # 上涨时卖出（可能错过收益）
            reward -= 0.05
        elif price_change < -0.01 and action == 1:  # 下跌时买入（可能接飞刀）
            reward -= 0.05
        
        # 破产惩罚
        if self.cash <= 0:
            reward -= 10
        
        return reward
