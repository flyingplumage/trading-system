"""
模型导出服务
支持导出为 ONNX、TensorRT 等格式
"""

import os
import torch
import onnx
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticPolicy


class ModelExporter:
    """模型导出器"""
    
    def __init__(self, export_dir: str = "backend/shared/models/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_onnx(
        self,
        model_path: str,
        output_name: str = None,
        opset_version: int = 11
    ) -> Dict:
        """
        导出 PPO 模型为 ONNX 格式
        
        Args:
            model_path: 原始模型路径 (.zip)
            output_name: 输出文件名
            opset_version: ONNX opset 版本
        
        Returns:
            导出信息
        """
        try:
            # 加载模型
            model = PPO.load(model_path)
            
            # 生成输出文件名
            if not output_name:
                base_name = Path(model_path).stem
                output_name = f"{base_name}_onnx"
            
            output_path = self.export_dir / f"{output_name}.onnx"
            
            # 创建示例输入
            # PPO 的输入是观察空间，假设是 (batch_size, obs_dim)
            obs_dim = model.observation_space.shape[0]
            dummy_input = torch.randn(1, obs_dim)
            
            # 导出为 ONNX
            torch.onnx.export(
                model.policy,
                dummy_input,
                str(output_path),
                opset_version=opset_version,
                input_names=['observation'],
                output_names=['action', 'action_prob', 'value'],
                dynamic_axes={
                    'observation': {0: 'batch_size'},
                    'action': {0: 'batch_size'},
                    'action_prob': {0: 'batch_size'},
                    'value': {0: 'batch_size'}
                }
            )
            
            # 验证导出的模型
            onnx_model = onnx.load(str(output_path))
            onnx.checker.check_model(onnx_model)
            
            # 获取模型信息
            model_info = {
                'original_path': model_path,
                'exported_path': str(output_path),
                'format': 'onnx',
                'opset_version': opset_version,
                'input_shape': [1, obs_dim],
                'output_shapes': {
                    'action': [1, model.action_space.n],
                    'action_prob': [1, model.action_space.n],
                    'value': [1, 1]
                },
                'file_size': output_path.stat().st_size,
                'exported_at': datetime.now().isoformat()
            }
            
            print(f"[ModelExporter] 模型已导出：{output_path}")
            print(f"  - 格式：ONNX")
            print(f"  - 大小：{output_path.stat().st_size / 1024:.2f} KB")
            
            return model_info
            
        except Exception as e:
            print(f"[ModelExporter] 导出失败：{e}")
            raise
    
    def export_to_torchscript(
        self,
        model_path: str,
        output_name: str = None
    ) -> Dict:
        """
        导出 PPO 模型为 TorchScript 格式
        
        Args:
            model_path: 原始模型路径 (.zip)
            output_name: 输出文件名
        
        Returns:
            导出信息
        """
        try:
            # 加载模型
            model = PPO.load(model_path)
            
            # 生成输出文件名
            if not output_name:
                base_name = Path(model_path).stem
                output_name = f"{base_name}_torchscript"
            
            output_path = self.export_dir / f"{output_name}.pt"
            
            # 创建示例输入
            obs_dim = model.observation_space.shape[0]
            dummy_input = torch.randn(1, obs_dim)
            
            # 导出为 TorchScript
            traced_model = torch.jit.trace(model.policy, dummy_input)
            traced_model.save(str(output_path))
            
            # 获取模型信息
            model_info = {
                'original_path': model_path,
                'exported_path': str(output_path),
                'format': 'torchscript',
                'input_shape': [1, obs_dim],
                'file_size': output_path.stat().st_size,
                'exported_at': datetime.now().isoformat()
            }
            
            print(f"[ModelExporter] 模型已导出：{output_path}")
            print(f"  - 格式：TorchScript")
            print(f"  - 大小：{output_path.stat().st_size / 1024:.2f} KB")
            
            return model_info
            
        except Exception as e:
            print(f"[ModelExporter] 导出失败：{e}")
            raise
    
    def list_exports(self) -> list:
        """列出所有导出的模型"""
        exports = []
        for file in self.export_dir.glob("*"):
            if file.suffix in ['.onnx', '.pt', '.engine']:
                exports.append({
                    'name': file.name,
                    'format': file.suffix[1:],
                    'size': file.stat().st_size,
                    'created_at': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
        return exports


# 全局导出器实例
model_exporter = ModelExporter()
