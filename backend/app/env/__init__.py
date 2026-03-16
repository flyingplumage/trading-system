"""
交易环境模块
- 内置示例环境（演示用）
- 支持用户上传自定义环境
"""

from .base import TradingEnvBase
from .momentum_env import MomentumEnv
from .mean_reversion_env import MeanReversionEnv
from .breakout_env import BreakoutEnv

# 内置环境注册表
BUILTIN_ENVS = {
    'momentum': MomentumEnv,
    'mean_reversion': MeanReversionEnv,
    'breakout': BreakoutEnv,
}

def get_env_class(env_name: str):
    """获取环境类"""
    if env_name in BUILTIN_ENVS:
        return BUILTIN_ENVS[env_name]
    raise ValueError(f"未知环境：{env_name}")

def list_envs():
    """列出所有可用环境"""
    return list(BUILTIN_ENVS.keys())

__all__ = [
    'TradingEnvBase',
    'MomentumEnv',
    'MeanReversionEnv',
    'BreakoutEnv',
    'get_env_class',
    'list_envs',
]
