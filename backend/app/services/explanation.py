"""
模型解释服务
使用 SHAP 和 LIME 解释模型决策
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    import lime
    import lime.lime_tabular
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False


class ModelExplainer:
    """模型解释器"""
    
    def __init__(self):
        self.explainers = {}
        self.feature_names = [
            'close', 'open', 'high', 'low', 'volume',
            'momentum', 'volatility', 'rsi', 'macd', 'bollinger'
        ]
        self.class_names = ['sell', 'hold', 'buy']
    
    def explain_with_shap(
        self,
        model,
        X_train: np.ndarray,
        X_test: np.ndarray,
        n_samples: int = 100
    ) -> Dict:
        """
        使用 SHAP 解释模型
        
        Args:
            model: 训练好的模型
            X_train: 训练数据
            X_test: 测试数据
            n_samples: 样本数
        
        Returns:
            SHAP 解释结果
        """
        if not SHAP_AVAILABLE:
            return {'error': 'SHAP 未安装'}
        
        try:
            # 创建 SHAP 解释器
            explainer = shap.KernelExplainer(
                model.predict,
                X_train[:n_samples]
            )
            
            # 计算 SHAP 值
            shap_values = explainer.shap_values(
                X_test[:10],
                nsamples=100
            )
            
            # 汇总统计
            if isinstance(shap_values, list):
                # 多分类情况
                mean_shap = [np.mean(np.abs(sv), axis=0) for sv in shap_values]
                shap_summary = {
                    class_name: self._get_feature_importance(mean_shap[i])
                    for i, class_name in enumerate(self.class_names)
                }
            else:
                # 二分类或回归
                mean_shap = np.mean(np.abs(shap_values), axis=0)
                shap_summary = self._get_feature_importance(mean_shap)
            
            return {
                'method': 'SHAP',
                'feature_importance': shap_summary,
                'shap_values_shape': self._get_shape(shap_values),
                'base_values': explainer.expected_value.tolist() if hasattr(explainer.expected_value, 'tolist') else float(explainer.expected_value),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'SHAP 解释失败：{str(e)}'}
    
    def explain_with_lime(
        self,
        model,
        X_train: np.ndarray,
        instance: np.ndarray,
        n_features: int = 5
    ) -> Dict:
        """
        使用 LIME 解释单个预测
        
        Args:
            model: 训练好的模型
            X_train: 训练数据
            instance: 单个样本
            n_features: 显示的特征数
        
        Returns:
            LIME 解释结果
        """
        if not LIME_AVAILABLE:
            return {'error': 'LIME 未安装'}
        
        try:
            # 创建 LIME 解释器
            explainer = lime.lime_tabular.LimeTabularExplainer(
                X_train,
                feature_names=self.feature_names,
                class_names=self.class_names,
                mode='classification'
            )
            
            # 解释单个实例
            explanation = explainer.explain_instance(
                instance,
                model.predict_proba,
                num_features=n_features
            )
            
            # 提取解释
            explanations_by_class = {}
            for class_idx, class_name in enumerate(self.class_names):
                exp = explanation.local_exp.get(class_idx, [])
                explanations_by_class[class_name] = [
                    {
                        'feature': self.feature_names[idx] if idx < len(self.feature_names) else f'feature_{idx}',
                        'weight': weight
                    }
                    for idx, weight in exp
                ]
            
            return {
                'method': 'LIME',
                'explanations': explanations_by_class,
                'predicted_class': self.class_names[explanation.predicted_label],
                'predicted_prob': explanation.predict_proba.tolist(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'LIME 解释失败：{str(e)}'}
    
    def explain_feature_importance(
        self,
        model,
        X_train: np.ndarray,
        method: str = 'shap'
    ) -> Dict:
        """
        解释特征重要性
        
        Args:
            model: 训练好的模型
            X_train: 训练数据
            method: 解释方法 (shap/permutation)
        
        Returns:
            特征重要性
        """
        try:
            if method == 'shap' and SHAP_AVAILABLE:
                result = self.explain_with_shap(model, X_train, X_train[:50])
                if 'error' not in result:
                    return {
                        'method': 'SHAP',
                        'feature_importance': result['feature_importance'],
                        'timestamp': datetime.now().isoformat()
                    }
            
            # 使用排列重要性
            importance = self._permutation_importance(model, X_train)
            return {
                'method': 'Permutation',
                'feature_importance': importance,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'特征重要性解释失败：{str(e)}'}
    
    def explain_decision_boundary(
        self,
        model,
        X_train: np.ndarray,
        feature1_idx: int = 0,
        feature2_idx: int = 1
    ) -> Dict:
        """
        解释决策边界
        
        Args:
            model: 训练好的模型
            X_train: 训练数据
            feature1_idx: 第一个特征索引
            feature2_idx: 第二个特征索引
        
        Returns:
            决策边界数据
        """
        try:
            # 生成网格
            x1_min, x1_max = X_train[:, feature1_idx].min(), X_train[:, feature1_idx].max()
            x2_min, x2_max = X_train[:, feature2_idx].min(), X_train[:, feature2_idx].max()
            
            xx1, xx2 = np.meshgrid(
                np.linspace(x1_min, x1_max, 50),
                np.linspace(x2_min, x2_max, 50)
            )
            
            # 预测
            grid_points = np.c_[xx1.ravel(), xx2.ravel()]
            
            # 补充其他特征为均值
            full_grid = np.zeros((grid_points.shape[0], X_train.shape[1]))
            full_grid[:, feature1_idx] = grid_points[:, 0]
            full_grid[:, feature2_idx] = grid_points[:, 1]
            
            for i in range(X_train.shape[1]):
                if i not in [feature1_idx, feature2_idx]:
                    full_grid[:, i] = X_train[:, i].mean()
            
            predictions = model.predict(full_grid)
            
            return {
                'feature1': self.feature_names[feature1_idx] if feature1_idx < len(self.feature_names) else f'feature_{feature1_idx}',
                'feature2': self.feature_names[feature2_idx] if feature2_idx < len(self.feature_names) else f'feature_{feature2_idx}',
                'x1_range': [float(x1_min), float(x1_max)],
                'x2_range': [float(x2_min), float(x2_max)],
                'predictions': predictions.tolist(),
                'grid_shape': [50, 50],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'决策边界解释失败：{str(e)}'}
    
    def _get_feature_importance(self, shap_values: np.ndarray) -> Dict:
        """获取特征重要性"""
        importance = {}
        for i, val in enumerate(shap_values):
            feature_name = self.feature_names[i] if i < len(self.feature_names) else f'feature_{i}'
            importance[feature_name] = float(val)
        
        # 按重要性排序
        sorted_importance = dict(
            sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)
        )
        
        return sorted_importance
    
    def _get_shape(self, shap_values) -> Dict:
        """获取 SHAP 值形状"""
        if isinstance(shap_values, list):
            return {
                'type': 'list',
                'length': len(shap_values),
                'each_shape': [sv.shape for sv in shap_values]
            }
        else:
            return {
                'type': 'array',
                'shape': list(shap_values.shape)
            }
    
    def _permutation_importance(
        self,
        model,
        X_train: np.ndarray,
        n_repeats: int = 10
    ) -> Dict:
        """排列重要性"""
        base_score = np.mean(model.predict(X_train))
        importance = {}
        
        for i in range(X_train.shape[1]):
            scores = []
            for _ in range(n_repeats):
                X_permuted = X_train.copy()
                np.random.shuffle(X_permuted[:, i])
                score = np.mean(model.predict(X_permuted))
                scores.append(abs(base_score - score))
            
            feature_name = self.feature_names[i] if i < len(self.feature_names) else f'feature_{i}'
            importance[feature_name] = float(np.mean(scores))
        
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


# 全局解释器实例
model_explainer = ModelExplainer()
