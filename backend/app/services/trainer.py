"""
真实 PPO 训练服务
基于 Stable Baselines3
支持 SQLite + DuckDB 混合存储
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import pandas as pd
import numpy as np

# ML 库
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.evaluation import evaluate_policy

# 本地环境
from app.env import get_env_class, list_envs
from app.db import database

# DuckDB 分析存储（可选）
try:
    from app.db.duckdb_analytics import init_db as duckdb_init, insert_metrics as duckdb_insert
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False


class TrainingCallback(BaseCallback):
    """训练回调 - 实时上报进度（支持 SQLite + DuckDB 双写）"""
    
    def __init__(self, exp_id: str, task_id: int, total_steps: int, eval_freq: int = 1000):
        super().__init__()
        self.exp_id = exp_id
        self.task_id = task_id
        self.total_steps = total_steps
        self.eval_freq = eval_freq
        self.start_time = time.time()
        self.best_reward = -float('inf')
        self.metrics_buffer = []  # DuckDB 批量写入缓冲
        
        # 初始化 DuckDB
        if DUCKDB_AVAILABLE:
            try:
                duckdb_init()
                print("[Trainer] DuckDB 分析库已初始化")
            except Exception as e:
                print(f"[Trainer] DuckDB 初始化失败：{e}，将仅使用 SQLite")
    
    def _on_step(self) -> bool:
        # 每 eval_freq 步上报一次
        if self.n_calls % self.eval_freq == 0:
            elapsed = (time.time() - self.start_time) / 60
            progress = (self.n_calls / self.total_steps) * 100
            
            # 获取当前指标
            infos = self.locals.get('infos', [])
            if infos:
                latest_info = infos[-1]
                portfolio_value = latest_info.get('portfolio_value', 0)
                cash = latest_info.get('cash', 0)
                position = latest_info.get('position', 0)
            else:
                portfolio_value = 0
                cash = 0
                position = 0
            
            # 构建指标数据
            metrics = {
                'step': int(self.n_calls),
                'progress': progress,
                'portfolio_value': portfolio_value,
                'cash': cash,
                'position': position,
                'elapsed_minutes': elapsed,
                'reward': float(self.locals.get('rewards', [0])[-1]) if 'rewards' in self.locals else 0
            }
            
            # 更新 SQLite（元数据）
            database.update_experiment(self.exp_id, metrics=json.dumps(metrics))
            database.update_training_task(
                self.task_id,
                result=json.dumps(metrics)
            )
            
            # DuckDB 双写（分析数据）
            if DUCKDB_AVAILABLE:
                try:
                    # 添加到缓冲
                    duckdb_metric = {
                        'id': int(time.time() * 1000) + self.n_calls,  # 唯一 ID
                        'experiment_id': self.exp_id,
                        'step': int(self.n_calls),
                        'progress': progress,
                        'reward': metrics['reward'],
                        'portfolio_value': portfolio_value,
                        'cash': cash,
                        'position': position,
                        'created_at': datetime.now()
                    }
                    self.metrics_buffer.append(duckdb_metric)
                    
                    # 每 10 次上报批量写入一次
                    if len(self.metrics_buffer) >= 10:
                        duckdb_insert(self.metrics_buffer)
                        self.metrics_buffer = []
                except Exception as e:
                    print(f"[Trainer] DuckDB 写入失败：{e}，继续使用 SQLite")
            
            print(f"[Trainer] 进度：{progress:.1f}%, 步数：{self.n_calls}/{self.total_steps}, "
                  f"组合价值：{portfolio_value:.2f}, 耗时：{elapsed:.1f}分钟")
        
        return True
    
    def _on_training_end(self) -> None:
        # 训练完成
        metrics = {
            'step': int(self.total_steps),
            'progress': 100.0,
            'completed': True
        }
        database.update_experiment(self.exp_id, metrics=json.dumps(metrics), status='completed')
        
        # 刷新 DuckDB 缓冲区
        if DUCKDB_AVAILABLE and self.metrics_buffer:
            try:
                duckdb_insert(self.metrics_buffer)
                print(f"[Trainer] DuckDB 缓冲区已刷新 ({len(self.metrics_buffer)} 条)")
            except Exception as e:
                print(f"[Trainer] DuckDB 刷新失败：{e}")
        
        print(f"[Trainer] 训练完成，总步数：{self.total_steps}")


class PPOTrainer:
    """PPO 训练器"""
    
    def __init__(self):
        self.model_dir = Path(__file__).parent.parent.parent / "shared" / "models"
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def train(
        self,
        strategy: str,
        exp_id: str,
        task_id: int,
        steps: int = 10000,
        learning_rate: float = 3e-5,
        env_name: str = 'momentum',
        stock_code: str = '000001.SZ',
        initial_cash: float = 1000000.0
    ):
        """
        训练 PPO 模型
        
        Args:
            strategy: 策略名称
            exp_id: 实验 ID
            task_id: 任务 ID
            steps: 训练步数
            learning_rate: 学习率
            env_name: 环境名称（momentum/mean_reversion/breakout）
            stock_code: 股票代码
            initial_cash: 初始资金
        """
        print(f"[Trainer] 开始训练 - 策略：{strategy}, 环境：{env_name}, 步数：{steps}")
        
        # 更新任务状态
        database.update_training_task(task_id, status='running')
        
        try:
            # 1. 获取数据
            from app.services.data import DataService
            data_service = DataService()
            
            print(f"[Trainer] 获取股票数据：{stock_code}")
            df = data_service.get_price_data(
                stock_code=stock_code,
                start_date=(datetime.now() - pd.Timedelta(days=365)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                auto_download=True
            )
            
            if df.empty:
                raise Exception(f"无法获取股票数据：{stock_code}")
            
            print(f"[Trainer] 获取到 {len(df)} 条数据")
            
            # 2. 创建环境
            print(f"[Trainer] 创建交易环境：{env_name}")
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
            
            # 3. 创建 PPO 模型
            print(f"[Trainer] 创建 PPO 模型，学习率：{learning_rate}")
            model = PPO(
                "MlpPolicy",
                env,
                learning_rate=learning_rate,
                n_steps=1024,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=0.01,
                verbose=1
            )
            
            # 4. 训练
            print(f"[Trainer] 开始训练，总步数：{steps}")
            callback = TrainingCallback(exp_id, task_id, steps)
            
            model.learn(
                total_timesteps=steps,
                callback=callback,
                log_interval=100
            )
            
            # 5. 保存模型
            model_path = self.model_dir / f"{strategy}_{exp_id}.zip"
            model.save(str(model_path))
            print(f"[Trainer] 模型已保存：{model_path}")
            
            # 6. 注册模型
            database.create_model(
                model_id=f"model_{exp_id}",
                name=f"{strategy}_model",
                strategy=strategy,
                version=1,
                experiment_id=exp_id,
                model_path=str(model_path)
            )
            
            # 7. 更新任务状态
            database.update_training_task(task_id, status='completed')
            
            print(f"[Trainer] 训练完成 - 策略：{strategy}")
            
            return str(model_path)
            
        except Exception as e:
            print(f"[Trainer] 训练失败：{e}")
            database.update_training_task(task_id, status='failed', error=str(e))
            raise


# 全局训练器实例
trainer = PPOTrainer()
