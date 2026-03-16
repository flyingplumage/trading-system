"""
K 线形态识别服务
识别常见的 K 线形态模式
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class CandlestickPattern:
    """K 线形态识别"""
    
    def __init__(self):
        # 形态定义
        self.patterns = {
            'hammer': self._detect_hammer,
            'shooting_star': self._detect_shooting_star,
            'engulfing_bull': self._detect_engulfing_bull,
            'engulfing_bear': self._detect_engulfing_bear,
            'doji': self._detect_doji,
            'morning_star': self._detect_morning_star,
            'evening_star': self._detect_evening_star,
            'three_white_soldiers': self._detect_three_white_soldiers,
            'three_black_crows': self._detect_three_black_crows,
        }
    
    def detect_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        检测所有 K 线形态
        
        Args:
            df: 包含 open/high/low/close 的 DataFrame
        
        Returns:
            包含形态信号的 DataFrame
        """
        result = df.copy()
        
        # 初始化所有形态列为 0
        for pattern_name in self.patterns.keys():
            result[f'pattern_{pattern_name}'] = 0
        
        # 检测每种形态
        for pattern_name, detector in self.patterns.items():
            signals = detector(result)
            result[f'pattern_{pattern_name}'] = signals
        
        return result
    
    def _detect_hammer(self, df: pd.DataFrame) -> pd.Series:
        """
        锤子线 (看涨反转)
        - 实体较小
        - 下影线至少是实体的 2 倍
        - 上影线很短或没有
        """
        body = abs(df['close'] - df['open'])
        lower_shadow = np.minimum(df['open'], df['close']) - df['low']
        upper_shadow = df['high'] - np.maximum(df['open'], df['close'])
        
        signal = (
            (lower_shadow >= 2 * body) &
            (upper_shadow <= body * 0.5) &
            (body > 0)
        )
        
        return signal.astype(int)
    
    def _detect_shooting_star(self, df: pd.DataFrame) -> pd.Series:
        """
        流星线 (看跌反转)
        - 实体较小
        - 上影线至少是实体的 2 倍
        - 下影线很短或没有
        """
        body = abs(df['close'] - df['open'])
        lower_shadow = np.minimum(df['open'], df['close']) - df['low']
        upper_shadow = df['high'] - np.maximum(df['open'], df['close'])
        
        signal = (
            (upper_shadow >= 2 * body) &
            (lower_shadow <= body * 0.5) &
            (body > 0)
        )
        
        return signal.astype(int)
    
    def _detect_engulfing_bull(self, df: pd.DataFrame) -> pd.Series:
        """
        看涨吞并形态
        - 第一根是阴线
        - 第二根是阳线
        - 第二根实体吞并第一根实体
        """
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        
        is_bullish = df['close'] > df['open']
        is_bearish_prev = prev_close < prev_open
        
        engulfing = (
            (df['open'] < prev_close) &
            (df['close'] > prev_open)
        )
        
        signal = is_bullish & is_bearish_prev & engulfing
        
        return signal.astype(int)
    
    def _detect_engulfing_bear(self, df: pd.DataFrame) -> pd.Series:
        """
        看跌吞并形态
        - 第一根是阳线
        - 第二根是阴线
        - 第二根实体吞并第一根实体
        """
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        
        is_bearish = df['close'] < df['open']
        is_bullish_prev = prev_close > prev_open
        
        engulfing = (
            (df['open'] > prev_close) &
            (df['close'] < prev_open)
        )
        
        signal = is_bearish & is_bullish_prev & engulfing
        
        return signal.astype(int)
    
    def _detect_doji(self, df: pd.DataFrame) -> pd.Series:
        """
        十字星
        - 开盘价和收盘价非常接近
        """
        body = abs(df['close'] - df['open'])
        avg_body = body.rolling(window=20).mean()
        
        signal = body <= (avg_body * 0.1)
        
        return signal.astype(int)
    
    def _detect_morning_star(self, df: pd.DataFrame) -> pd.Series:
        """
        早晨之星 (看涨反转)
        - 第一根是大阴线
        - 第二根是小实体 (星)
        - 第三根是大阳线
        """
        body = abs(df['close'] - df['open'])
        avg_body = body.rolling(window=20).mean()
        
        # 第一根大阴线
        prev1_open = df['open'].shift(1)
        prev1_close = df['close'].shift(1)
        large_bear1 = (prev1_close < prev1_open) & (prev1_open - prev1_close > avg_body.shift(1) * 1.5)
        
        # 第二根小实体 (星)
        prev2_open = df['open'].shift(2)
        prev2_close = df['close'].shift(2)
        small_body2 = body.shift(2) <= avg_body.shift(2) * 0.5
        
        # 第三根大阳线
        large_bull = (df['close'] > df['open']) & (df['close'] - df['open'] > avg_body * 1.5)
        
        signal = large_bear1 & small_body2 & large_bull
        
        return signal.astype(int)
    
    def _detect_evening_star(self, df: pd.DataFrame) -> pd.Series:
        """
        黄昏之星 (看跌反转)
        - 第一根是大阳线
        - 第二根是小实体 (星)
        - 第三根是大阴线
        """
        body = abs(df['close'] - df['open'])
        avg_body = body.rolling(window=20).mean()
        
        # 第一根大阳线
        prev1_open = df['open'].shift(1)
        prev1_close = df['close'].shift(1)
        large_bull1 = (prev1_close > prev1_open) & (prev1_close - prev1_open > avg_body.shift(1) * 1.5)
        
        # 第二根小实体 (星)
        small_body2 = body.shift(2) <= avg_body.shift(2) * 0.5
        
        # 第三根大阴线
        large_bear = (df['close'] < df['open']) & (df['open'] - df['close'] > avg_body * 1.5)
        
        signal = large_bull1 & small_body2 & large_bear
        
        return signal.astype(int)
    
    def _detect_three_white_soldiers(self, df: pd.DataFrame) -> pd.Series:
        """
        三白兵 (连续三根阳线，看涨)
        """
        bull1 = (df['close'] > df['open'])
        bull2 = (df['close'].shift(1) > df['open'].shift(1))
        bull3 = (df['close'].shift(2) > df['open'].shift(2))
        
        # 每根阳线的收盘价都高于前一根
        higher_close = (
            (df['close'] > df['close'].shift(1)) &
            (df['close'].shift(1) > df['close'].shift(2))
        )
        
        signal = bull1 & bull2 & bull3 & higher_close
        
        return signal.astype(int)
    
    def _detect_three_black_crows(self, df: pd.DataFrame) -> pd.Series:
        """
        三乌鸦 (连续三根阴线，看跌)
        """
        bear1 = (df['close'] < df['open'])
        bear2 = (df['close'].shift(1) < df['open'].shift(1))
        bear3 = (df['close'].shift(2) < df['open'].shift(2))
        
        # 每根阴线的收盘价都低于前一根
        lower_close = (
            (df['close'] < df['close'].shift(1)) &
            (df['close'].shift(1) < df['close'].shift(2))
        )
        
        signal = bear1 & bear2 & bear3 & lower_close
        
        return signal.astype(int)
    
    def get_pattern_summary(self, df: pd.DataFrame, window: int = 100) -> Dict:
        """
        获取形态统计摘要
        
        Args:
            df: 包含形态信号的 DataFrame
            window: 统计窗口
        
        Returns:
            形态统计信息
        """
        pattern_cols = [col for col in df.columns if col.startswith('pattern_')]
        
        summary = {}
        for col in pattern_cols:
            pattern_name = col.replace('pattern_', '')
            recent_signals = df[col].iloc[-window:].sum()
            total_signals = df[col].sum()
            
            summary[pattern_name] = {
                'recent_count': int(recent_signals),
                'total_count': int(total_signals),
                'last_signal': int(df[col].iloc[-1]) if len(df) > 0 else 0
            }
        
        return summary


# 全局形态识别器
candlestick_pattern = CandlestickPattern()
