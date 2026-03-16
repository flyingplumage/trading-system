"""
板块分析服务
分析行业板块、概念板块的表现
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class SectorAnalyzer:
    """板块分析器"""
    
    def __init__(self, data_dir: str = "backend/shared/data/sectors"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 板块分类
        self.sector_types = {
            'industry': '行业板块',
            'concept': '概念板块',
            'region': '地区板块'
        }
    
    def get_sector_list(self, sector_type: str = 'industry') -> List[Dict]:
        """
        获取板块列表
        
        Args:
            sector_type: 板块类型 (industry/concept/region)
        
        Returns:
            板块列表
        """
        # 示例板块数据 (实际应从数据库或 API 获取)
        sectors = {
            'industry': [
                {'code': 'BK0491', 'name': '半导体', 'stock_count': 150},
                {'code': 'BK0492', 'name': '计算机设备', 'stock_count': 120},
                {'code': 'BK0493', 'name': '软件开发', 'stock_count': 180},
                {'code': 'BK0494', 'name': '医药生物', 'stock_count': 200},
                {'code': 'BK0495', 'name': '食品饮料', 'stock_count': 100},
                {'code': 'BK0496', 'name': '新能源', 'stock_count': 160},
                {'code': 'BK0497', 'name': '汽车', 'stock_count': 140},
                {'code': 'BK0498', 'name': '金融', 'stock_count': 80},
            ],
            'concept': [
                {'code': 'BK0501', 'name': '人工智能', 'stock_count': 200},
                {'code': 'BK0502', 'name': '芯片', 'stock_count': 180},
                {'code': 'BK0503', 'name': '5G', 'stock_count': 150},
                {'code': 'BK0504', 'name': '新能源车', 'stock_count': 170},
                {'code': 'BK0505', 'name': '光伏', 'stock_count': 130},
            ],
            'region': [
                {'code': 'BK0601', 'name': '北京', 'stock_count': 450},
                {'code': 'BK0602', 'name': '上海', 'stock_count': 400},
                {'code': 'BK0603', 'name': '深圳', 'stock_count': 500},
                {'code': 'BK0604', 'name': '浙江', 'stock_count': 350},
            ]
        }
        
        return sectors.get(sector_type, [])
    
    def get_sector_stocks(self, sector_code: str) -> List[str]:
        """
        获取板块成分股
        
        Args:
            sector_code: 板块代码
        
        Returns:
            股票代码列表
        """
        # 示例数据 (实际应从数据库获取)
        sector_stocks = {
            'BK0491': ['000001.SZ', '000002.SZ', '002594.SZ', '300750.SZ'],
            'BK0492': ['000001.SZ', '000002.SZ', '600519.SH'],
            'BK0496': ['002594.SZ', '300750.SZ'],
            'BK0501': ['000001.SZ', '000002.SZ', '002594.SZ', '300750.SZ', '600519.SH'],
            'BK0504': ['002594.SZ', '300750.SZ'],
        }
        
        return sector_stocks.get(sector_code, [])
    
    def analyze_sector_performance(
        self,
        sector_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        分析板块表现
        
        Args:
            sector_code: 板块代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            板块表现分析
        """
        stocks = self.get_sector_stocks(sector_code)
        
        if not stocks:
            return {
                'sector_code': sector_code,
                'error': '板块无成分股'
            }
        
        # 示例分析 (实际应计算真实数据)
        performance = {
            'sector_code': sector_code,
            'stock_count': len(stocks),
            'stocks': stocks,
            'metrics': {
                'avg_return_1d': 0.015,
                'avg_return_5d': 0.032,
                'avg_return_20d': 0.078,
                'avg_volume_ratio': 1.2,
                'up_count': int(len(stocks) * 0.6),
                'down_count': int(len(stocks) * 0.4),
                'limit_up_count': int(len(stocks) * 0.1),
                'limit_down_count': int(len(stocks) * 0.05)
            },
            'top_gainers': stocks[:3],
            'top_losers': stocks[-2:],
            'analysis_time': datetime.now().isoformat()
        }
        
        return performance
    
    def get_sector_ranking(
        self,
        sector_type: str = 'industry',
        metric: str = 'return_1d',
        top_n: int = 10
    ) -> List[Dict]:
        """
        获取板块排名
        
        Args:
            sector_type: 板块类型
            metric: 排名指标 (return_1d/return_5d/volume)
            top_n: 返回前 N 个
        
        Returns:
            板块排名列表
        """
        sectors = self.get_sector_list(sector_type)
        
        # 示例排名数据 (实际应计算真实数据)
        import random
        for sector in sectors:
            sector['return_1d'] = random.uniform(-0.05, 0.05)
            sector['return_5d'] = random.uniform(-0.1, 0.1)
            sector['return_20d'] = random.uniform(-0.2, 0.2)
            sector['volume_ratio'] = random.uniform(0.5, 2.0)
        
        # 排序
        reverse = metric.startswith('return')
        sorted_sectors = sorted(
            sectors,
            key=lambda x: x.get(metric, 0),
            reverse=reverse
        )
        
        return sorted_sectors[:top_n]
    
    def get_sector_correlation(
        self,
        sector_codes: List[str],
        window: int = 20
    ) -> Dict:
        """
        计算板块相关性
        
        Args:
            sector_codes: 板块代码列表
            window: 计算窗口
        
        Returns:
            相关性矩阵
        """
        # 示例相关性矩阵 (实际应计算真实数据)
        n = len(sector_codes)
        corr_matrix = np.eye(n)
        
        # 填充示例相关性
        for i in range(n):
            for j in range(i+1, n):
                corr = np.random.uniform(0.3, 0.8)
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr
        
        # 转换为 DataFrame
        corr_df = pd.DataFrame(
            corr_matrix,
            index=sector_codes,
            columns=sector_codes
        )
        
        return {
            'sectors': sector_codes,
            'correlation_matrix': corr_df.to_dict(),
            'window': window
        }
    
    def get_sector_rotation(self, window: int = 5) -> Dict:
        """
        获取板块轮动分析
        
        Args:
            window: 分析窗口 (天)
        
        Returns:
            板块轮动分析
        """
        # 获取行业板块
        sectors = self.get_sector_list('industry')
        
        # 示例轮动分析
        rotation = {
            'inflow_sectors': sectors[:3],  # 资金流入
            'outflow_sectors': sectors[-2:],  # 资金流出
            'hot_sectors': sectors[1:4],  # 热门板块
            'cold_sectors': sectors[-3:],  # 冷门板块
            'rotation_speed': 'fast',  # 轮动速度
            'analysis_time': datetime.now().isoformat()
        }
        
        return rotation


# 全局板块分析器
sector_analyzer = SectorAnalyzer()
