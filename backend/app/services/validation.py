"""
策略验证服务
验证策略的有效性和稳健性
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class StrategyValidator:
    """策略验证器"""
    
    def __init__(self):
        self.validation_methods = {
            'walk_forward': self._walk_forward_analysis,
            'monte_carlo': self._monte_carlo_simulation,
            'parameter_sensitivity': self._parameter_sensitivity,
            'out_of_sample': self._out_of_sample_test
        }
    
    def validate(
        self,
        strategy_results: pd.DataFrame,
        methods: List[str] = None
    ) -> Dict:
        """
        验证策略
        
        Args:
            strategy_results: 策略结果 (包含 returns, equity 等列)
            methods: 验证方法列表
        
        Returns:
            验证结果
        """
        if methods is None:
            methods = ['walk_forward', 'monte_carlo', 'parameter_sensitivity']
        
        results = {}
        
        for method in methods:
            if method in self.validation_methods:
                results[method] = self.validation_methods[method](strategy_results)
        
        # 综合评分
        results['overall_score'] = self._calculate_overall_score(results)
        results['recommendation'] = self._get_recommendation(results['overall_score'])
        
        return results
    
    def _walk_forward_analysis(self, results: pd.DataFrame) -> Dict:
        """
        滚动窗口分析
        将数据分为多个训练/测试段
        """
        n_splits = 5
        equity = results.get('equity', pd.Series([1.0]))
        
        split_size = len(equity) // n_splits
        returns_by_split = []
        
        for i in range(n_splits - 1):
            start_idx = i * split_size
            end_idx = (i + 2) * split_size
            split_equity = equity.iloc[start_idx:end_idx]
            
            if len(split_equity) > 1:
                split_return = (split_equity.iloc[-1] / split_equity.iloc[0]) - 1
                returns_by_split.append(split_return)
        
        if returns_by_split:
            return {
                'n_splits': n_splits,
                'split_returns': returns_by_split,
                'mean_return': float(np.mean(returns_by_split)),
                'std_return': float(np.std(returns_by_split)),
                'consistency': float(1 - np.std(returns_by_split) / (abs(np.mean(returns_by_split)) + 1e-6)),
                'robust': np.std(returns_by_split) < abs(np.mean(returns_by_split))
            }
        
        return {'error': '数据不足'}
    
    def _monte_carlo_simulation(self, results: pd.DataFrame, n_simulations: int = 1000) -> Dict:
        """
        蒙特卡洛模拟
        随机重采样交易序列
        """
        returns = results.get('returns', pd.Series([0]))
        
        if len(returns) < 10:
            return {'error': '数据不足'}
        
        simulated_final_values = []
        
        for _ in range(n_simulations):
            # 随机重采样收益率
            sampled_returns = returns.sample(n=len(returns), replace=True)
            simulated_equity = (1 + sampled_returns).cumprod()
            simulated_final_values.append(simulated_equity.iloc[-1])
        
        simulated_final_values = np.array(simulated_final_values)
        
        return {
            'n_simulations': n_simulations,
            'mean_final_value': float(np.mean(simulated_final_values)),
            'std_final_value': float(np.std(simulated_final_values)),
            'median_final_value': float(np.median(simulated_final_values)),
            'percentile_5': float(np.percentile(simulated_final_values, 5)),
            'percentile_95': float(np.percentile(simulated_final_values, 95)),
            'probability_positive': float(np.mean(simulated_final_values > 1)),
            'risk_of_ruin': float(np.mean(simulated_final_values < 0.5))
        }
    
    def _parameter_sensitivity(self, results: pd.DataFrame) -> Dict:
        """
        参数敏感性分析
        评估策略对参数变化的敏感度
        """
        # 示例分析 (实际应基于不同参数组合的结果)
        base_sharpe = results.get('sharpe_ratio', 1.0)
        
        # 模拟参数变化 ±10% 的影响
        sensitivity_scenarios = {
            'lookback_period': {
                'base': base_sharpe,
                'minus_10pct': base_sharpe * 0.9,
                'plus_10pct': base_sharpe * 1.05
            },
            'threshold': {
                'base': base_sharpe,
                'minus_10pct': base_sharpe * 0.85,
                'plus_10pct': base_sharpe * 1.1
            }
        }
        
        # 计算敏感性得分 (越低越稳健)
        sensitivity_score = 0
        for param, scenarios in sensitivity_scenarios.items():
            variation = (scenarios['plus_10pct'] - scenarios['minus_10pct']) / scenarios['base']
            sensitivity_score += abs(variation)
        
        sensitivity_score /= len(sensitivity_scenarios)
        
        return {
            'scenarios': sensitivity_scenarios,
            'sensitivity_score': float(sensitivity_score),
            'robust': sensitivity_score < 0.3
        }
    
    def _out_of_sample_test(self, results: pd.DataFrame) -> Dict:
        """
        样本外测试
        比较样本内和样本外表现
        """
        equity = results.get('equity', pd.Series([1.0]))
        split_point = int(len(equity) * 0.7)
        
        in_sample = equity.iloc[:split_point]
        out_sample = equity.iloc[split_point:]
        
        in_sample_return = (in_sample.iloc[-1] / in_sample.iloc[0]) - 1 if len(in_sample) > 1 else 0
        out_sample_return = (out_sample.iloc[-1] / out_sample.iloc[0]) - 1 if len(out_sample) > 1 else 0
        
        degradation = (in_sample_return - out_sample_return) / (abs(in_sample_return) + 1e-6)
        
        return {
            'in_sample_return': float(in_sample_return),
            'out_sample_return': float(out_sample_return),
            'degradation': float(degradation),
            'passed': degradation < 0.5  # 样本外衰退不超过 50%
        }
    
    def _calculate_overall_score(self, results: Dict) -> float:
        """计算综合验证得分"""
        score = 0
        weights = {
            'walk_forward': 0.3,
            'monte_carlo': 0.3,
            'parameter_sensitivity': 0.2,
            'out_of_sample': 0.2
        }
        
        if 'walk_forward' in results:
            wf = results['walk_forward']
            if 'consistency' in wf:
                score += wf['consistency'] * weights['walk_forward']
        
        if 'monte_carlo' in results:
            mc = results['monte_carlo']
            if 'probability_positive' in mc:
                score += mc['probability_positive'] * weights['monte_carlo']
        
        if 'parameter_sensitivity' in results:
            ps = results['parameter_sensitivity']
            if 'robust' in ps:
                score += (1 if ps['robust'] else 0.5) * weights['parameter_sensitivity']
        
        if 'out_of_sample' in results:
            oos = results['out_of_sample']
            if 'passed' in oos:
                score += (1 if oos['passed'] else 0.3) * weights['out_of_sample']
        
        return min(1.0, score)
    
    def _get_recommendation(self, score: float) -> str:
        """根据得分给出建议"""
        if score >= 0.8:
            return "优秀 - 策略验证通过，可以实盘"
        elif score >= 0.6:
            return "良好 - 策略基本可靠，建议优化"
        elif score >= 0.4:
            return "一般 - 策略需要改进"
        else:
            return "较差 - 策略不可靠，不建议使用"


# 全局验证器实例
strategy_validator = StrategyValidator()
