"""
Tushare Pro 数据服务
- 股票列表获取
- 日线数据下载
- 分钟线数据下载
- 增量更新
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import pandas as pd
import requests
import yaml
from .checkpoint import CheckpointManager


class TushareService:
    """Tushare Pro 数据服务"""
    
    def __init__(self, token: str = None):
        """
        初始化 Tushare 服务
        
        Args:
            token: Tushare API Token，优先从环境变量读取
        """
        self.token = token or os.getenv('TUSHARE_TOKEN', '')
        self.api_url = "http://api.tushare.pro"
        
        # 数据目录
        self.base_dir = Path(__file__).parent.parent.parent / "shared" / "data"
        self.raw_dir = self.base_dir / "raw"
        self.features_dir = self.base_dir / "features"
        self.pool_file = self.base_dir / "pool" / "stock_pool.yaml"
        
        # 确保目录存在（处理符号链接情况）
        try:
            self.raw_dir.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        try:
            self.features_dir.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        try:
            self.pool_file.parent.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        
        # 请求限制
        self.last_request_time = 0
        self.min_request_interval = 60  # 60 秒（避免限流）
        self.api_call_count = 0
        
        # 检查点管理器
        self.checkpoint = CheckpointManager()
        
        print(f"[Tushare] 服务初始化完成，数据目录：{self.base_dir}")
    
    def _request(self, api_name: str, params: dict = None) -> dict:
        """
        发送 API 请求（带限流）
        
        Args:
            api_name: API 接口名称
            params: 请求参数
        
        Returns:
            API 响应数据
        """
        # 限流控制
        now = time.time()
        if now - self.last_request_time < self.min_request_interval:
            wait_time = self.min_request_interval - (now - self.last_request_time)
            print(f"[Tushare] 限流保护，等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
        
        # 构建请求
        payload = {
            "api_name": api_name,
            "token": self.token,
            "params": params or {},
            "fields": ""
        }
        
        # 发送请求
        response = requests.post(self.api_url, json=payload)
        self.last_request_time = time.time()
        self.api_call_count += 1
        
        # 解析响应
        result = response.json()
        code = result.get("code", 0)
        
        if code != 0:
            error_msg = result.get('msg', 'Unknown error')
            
            # 限流错误
            if '每分钟最多访问' in error_msg or '每小时最多访问' in error_msg or code == 40203:
                print(f"[Tushare] 触发限流，等待 60 秒后重试... (第 {self.api_call_count} 次调用)")
                time.sleep(60)
                # 重试一次
                response = requests.post(self.api_url, json=payload)
                result = response.json()
                code = result.get("code", 0)
                
                if code != 0:
                    raise Exception(f"Tushare API 错误：{result.get('msg')}")
            else:
                raise Exception(f"Tushare API 错误：{error_msg}")
        
        return result
    
    def get_stock_list(self, exchange: str = None) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            exchange: 交易所 SSE/SZSE/BSE
        
        Returns:
            股票列表 DataFrame
        """
        print(f"[Tushare] 获取股票列表，交易所：{exchange or '全部'}")
        
        params = {}
        if exchange:
            params['exchange'] = exchange
        
        result = self._request("stock_basic", params)
        
        # 解析数据 (Tushare 返回 data 而非 result)
        data = result.get('data') or result.get('result')
        if not data:
            raise Exception(f"Tushare API 返回数据格式异常：{result}")
        
        fields = data['fields']
        items = data['items']
        
        df = pd.DataFrame(items, columns=fields)
        
        print(f"[Tushare] 获取到 {len(df)} 只股票")
        return df
    
    def get_daily_data(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        获取日线数据（每日调用，适合训练）
        
        Args:
            ts_code: 股票代码（如 000001.SZ）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
        
        Returns:
            日线数据 DataFrame
        """
        print(f"[Tushare] 获取日线数据：{ts_code}")
        
        params = {
            "ts_code": ts_code,
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        result = self._request("daily", params)
        
        # 解析数据 (Tushare 返回 data 而非 result)
        data = result.get('data') or result.get('result')
        if not data:
            raise Exception(f"Tushare API 返回数据格式异常：{result}")
        
        fields = data['fields']
        items = data['items']
        
        if not items:
            return pd.DataFrame()
        
        df = pd.DataFrame(items, columns=fields)
        
        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        
        print(f"[Tushare] 获取到 {len(df)} 条记录")
        return df
    
    def get_min_data(
        self,
        ts_code: str,
        freq: str = 'D',
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        获取分钟线数据
        
        Args:
            ts_code: 股票代码（如 000001.SZ）
            freq: 周期 1/5/15/30/60 分钟
            start_date: 开始日期（YYYYMMDD HH:mm:ss 格式）
            end_date: 结束日期（YYYYMMDD HH:mm:ss 格式）
        
        Returns:
            分钟线数据 DataFrame
        
        注意：分钟线数据需要较高权限，免费版可能无法访问
        """
        print(f"[Tushare] 获取分钟线数据：{ts_code}, 周期：{freq}分钟")
        
        # 分钟线 API
        params = {
            "ts_code": ts_code,
            "freq": freq  # 1/5/15/30/60
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        try:
            result = self._request("stk_min", params)
            
            # 解析数据 (Tushare 返回 data 而非 result)
            data = result.get('data') or result.get('result')
            if not data:
                raise Exception(f"Tushare API 返回数据格式异常：{result}")
            
            fields = data['fields']
            items = data['items']
            
            if not items:
                return pd.DataFrame()
            
            df = pd.DataFrame(items, columns=fields)
            
            # 转换时间格式
            df['trade_time'] = pd.to_datetime(df['trade_time'])
            
            print(f"[Tushare] 获取到 {len(df)} 条分钟线记录")
            return df
            
        except Exception as e:
            print(f"[Tushare] 获取分钟线失败：{e}")
            # 返回空 DataFrame
            return pd.DataFrame()
    
    def update_stock_pool(self, exclude_st: bool = True, min_list_days: int = 60) -> List[str]:
        """
        更新股票池
        
        Args:
            exclude_st: 排除 ST 股票
            min_list_days: 最小上市天数
        
        Returns:
            股票列表
        """
        print("[Tushare] 更新股票池...")
        
        # 获取沪深股票列表
        sh_stocks = self.get_stock_list("SSE")
        sz_stocks = self.get_stock_list("SZSE")
        
        # 合并
        all_stocks = pd.concat([sh_stocks, sz_stocks], ignore_index=True)
        
        # 过滤条件
        if exclude_st:
            # 排除 ST、*ST
            all_stocks = all_stocks[~all_stocks['name'].str.contains('ST', na=False)]
        
        # 计算上市天数
        all_stocks['list_date'] = pd.to_datetime(all_stocks['list_date'], format='%Y%m%d')
        days_since_listing = (datetime.now() - all_stocks['list_date']).dt.days
        all_stocks = all_stocks[days_since_listing >= min_list_days]
        
        # 获取股票代码列表
        stock_list = all_stocks['ts_code'].tolist()
        
        # 保存到配置文件
        pool_config = {
            'meta': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'source': 'tushare',
                'version': '1.0'
            },
            'config': {
                'markets': ['SSE', 'SZSE'],
                'exclude_st': exclude_st,
                'min_list_days': min_list_days
            },
            'stocks': stock_list,
            'history': []
        }
        
        with open(self.pool_file, 'w', encoding='utf-8') as f:
            yaml.dump(pool_config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"[Tushare] 股票池更新完成，共 {len(stock_list)} 只股票")
        return stock_list
    
    def get_last_update_date(self, ts_code: str) -> Optional[str]:
        """
        获取股票最后更新日期
        
        Args:
            ts_code: 股票代码
        
        Returns:
            最后更新日期（YYYYMMDD 格式）
        """
        feature_file = self.features_dir / f"{ts_code.replace('.', '_')}.parquet"
        
        if not feature_file.exists():
            return None
        
        try:
            df = pd.read_parquet(feature_file)
            if df.empty:
                return None
            
            last_date = df['trade_date'].max()
            return last_date.strftime('%Y%m%d')
        except Exception as e:
            print(f"[Tushare] 读取最后更新日期失败：{e}")
            return None
    
    def detect_gaps(self, ts_code: str, threshold_days: int = 3) -> List[Dict]:
        """
        检测数据缺口
        
        Args:
            ts_code: 股票代码
            threshold_days: 缺口阈值（默认 3 天）
        
        Returns:
            缺口列表 [{'start': '20260101', 'end': '20260105', 'days': 3}, ...]
        """
        feature_file = self.features_dir / f"{ts_code.replace('.', '_')}.parquet"
        
        if not feature_file.exists():
            return []
        
        try:
            df = pd.read_parquet(feature_file)
            if df.empty:
                return []
            
            # 确保日期格式
            if not pd.api.types.is_datetime64_any_dtype(df['trade_date']):
                df['trade_date'] = pd.to_datetime(df['trade_date'])
            
            # 排序
            df_sorted = df.sort_values('trade_date').reset_index(drop=True)
            
            # 计算日期差
            date_diff = df_sorted['trade_date'].diff().dt.days
            
            # 找出缺口
            gaps = []
            for i in range(1, len(df_sorted)):
                diff = date_diff.iloc[i]
                if pd.notna(diff) and diff > threshold_days:
                    gap_start = df_sorted.iloc[i-1]['trade_date'] + timedelta(days=1)
                    gap_end = df_sorted.iloc[i]['trade_date'] - timedelta(days=1)
                    gaps.append({
                        'start': gap_start.strftime('%Y%m%d'),
                        'end': gap_end.strftime('%Y%m%d'),
                        'days': int(diff - 1)
                    })
            
            if gaps:
                print(f"[Tushare] {ts_code}: 发现 {len(gaps)} 个缺口")
            
            return gaps
        
        except Exception as e:
            print(f"[Tushare] 检测缺口失败：{e}")
            return []
    
    def get_local_data_range(self, ts_code: str) -> Dict:
        """
        获取本地数据范围
        
        Returns:
            {'start': '20260101', 'end': '20260320', 'total_days': 50}
        """
        feature_file = self.features_dir / f"{ts_code.replace('.', '_')}.parquet"
        
        if not feature_file.exists():
            return {'start': None, 'end': None, 'total_days': 0}
        
        try:
            df = pd.read_parquet(feature_file)
            if df.empty:
                return {'start': None, 'end': None, 'total_days': 0}
            
            # 确保日期格式
            if not pd.api.types.is_datetime64_any_dtype(df['trade_date']):
                df['trade_date'] = pd.to_datetime(df['trade_date'])
            
            start_date = df['trade_date'].min()
            end_date = df['trade_date'].max()
            total_days = (end_date - start_date).days + 1
            
            return {
                'start': start_date.strftime('%Y%m%d'),
                'end': end_date.strftime('%Y%m%d'),
                'total_days': total_days,
                'trade_days': len(df)
            }
        
        except Exception as e:
            print(f"[Tushare] 获取本地数据范围失败：{e}")
            return {'start': None, 'end': None, 'total_days': 0}
    
    def incremental_update(
        self,
        ts_code: str,
        end_date: str = None,
        fill_gaps: bool = True
    ) -> int:
        """
        增量更新股票数据（日线）- 带缺口检测
        
        Args:
            ts_code: 股票代码
            end_date: 结束日期（默认今天）
            fill_gaps: 是否自动填补缺口
        
        Returns:
            新增记录数
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        
        # 1. 检测并补充缺口（可选）
        if fill_gaps:
            gaps = self.detect_gaps(ts_code)
            if gaps:
                print(f"[Tushare] {ts_code}: 发现 {len(gaps)} 个缺口，开始补充...")
                for i, gap in enumerate(gaps):
                    print(f"[Tushare] 补充缺口 {i+1}/{len(gaps)}: {gap['start']} - {gap['end']}")
                    self._download_and_merge(ts_code, gap['start'], gap['end'])
        
        # 2. 获取最后更新日期
        last_date = self.get_last_update_date(ts_code)
        
        if last_date:
            # 增量更新：只获取最后更新日期之后的数据
            start_date = (datetime.strptime(last_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
            print(f"[Tushare] 增量更新：{ts_code}，从 {start_date} 到 {end_date}")
        else:
            # 全量更新：获取最近 1 年数据
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            print(f"[Tushare] 全量更新：{ts_code}，从 {start_date} 到 {end_date}")
        
        # 3. 检查是否需要更新
        if start_date > end_date:
            print(f"[Tushare] 数据已是最新：{ts_code}")
            return 0
        
        # 4. 获取日线数据并合并
        return self._download_and_merge(ts_code, start_date, end_date)
    
    def _download_and_merge(self, ts_code: str, start_date: str, end_date: str) -> int:
        """
        下载数据并合并到本地文件
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            总记录数
        """
        # 获取日线数据
        df = self.get_daily_data(ts_code, start_date, end_date)
        
        if df.empty:
            print(f"[Tushare] 无新数据可下载：{ts_code}")
            return 0
        
        # 合并现有数据
        feature_file = self.features_dir / f"{ts_code.replace('.', '_')}.parquet"
        
        if feature_file.exists():
            existing_df = pd.read_parquet(feature_file)
            df = pd.concat([existing_df, df], ignore_index=True)
            df = df.drop_duplicates(subset=['trade_date'], keep='last')
        
        # 按日期排序
        df = df.sort_values('trade_date')
        
        # 保存
        df.to_parquet(feature_file, index=False)
        
        print(f"[Tushare] 更新完成：{ts_code}，共 {len(df)} 条记录")
        return len(df)
    
    def update_all_stocks(self, limit: int = None) -> Dict[str, int]:
        """
        批量更新所有股票数据
        
        Args:
            limit: 限制更新数量（用于测试）
        
        Returns:
            更新统计
        """
        # 读取股票池
        if not self.pool_file.exists():
            print("[Tushare] 股票池不存在，先更新股票池")
            self.update_stock_pool()
        
        with open(self.pool_file, 'r', encoding='utf-8') as f:
            pool_config = yaml.safe_load(f)
        
        stock_list = pool_config.get('stocks', [])
        
        if limit:
            stock_list = stock_list[:limit]
        
        print(f"[Tushare] 开始批量更新 {len(stock_list)} 只股票...")
        
        # 更新统计
        stats = {
            'total': len(stock_list),
            'success': 0,
            'failed': 0,
            'new_records': 0
        }
        
        # 批量更新
        for i, ts_code in enumerate(stock_list):
            try:
                new_count = self.incremental_update(ts_code)
                stats['success'] += 1
                stats['new_records'] += new_count
                
                # 进度报告
                if (i + 1) % 10 == 0:
                    print(f"[Tushare] 进度：{i+1}/{len(stock_list)}")
                
            except Exception as e:
                print(f"[Tushare] 更新失败 {ts_code}: {e}")
                stats['failed'] += 1
            
            # 限流：每 10 次请求暂停 1 秒
            if (i + 1) % 10 == 0:
                time.sleep(1)
        
        print(f"[Tushare] 批量更新完成：成功 {stats['success']}, 失败 {stats['failed']}, 新增 {stats['new_records']} 条记录")
        return stats
    
    def check_data_availability(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        检查数据是否可用，返回缺失的日期范围
        
        Args:
            ts_code: 股票代码
            start_date: 需要的开始日期（YYYYMMDD）
            end_date: 需要的结束日期（YYYYMMDD）
        
        Returns:
            数据可用性信息
        """
        feature_file = self.features_dir / f"{ts_code.replace('.', '_')}.parquet"
        
        result = {
            'ts_code': ts_code,
            'has_data': False,
            'local_start': None,
            'local_end': None,
            'missing_start': start_date,
            'missing_end': end_date,
            'need_download': True
        }
        
        # 本地无文件
        if not feature_file.exists():
            print(f"[Tushare] 本地无数据：{ts_code}，需要下载 {start_date}-{end_date}")
            return result
        
        try:
            df = pd.read_parquet(feature_file)
            if df.empty:
                print(f"[Tushare] 本地数据为空：{ts_code}，需要下载")
                return result
            
            # 确保日期格式
            if not pd.api.types.is_datetime64_any_dtype(df['trade_date']):
                df['trade_date'] = pd.to_datetime(df['trade_date'])
            
            local_start = df['trade_date'].min().strftime('%Y%m%d')
            local_end = df['trade_date'].max().strftime('%Y%m%d')
            
            result['has_data'] = True
            result['local_start'] = local_start
            result['local_end'] = local_end
            
            # 判断是否需要更新
            if local_end >= end_date and local_start <= start_date:
                # 数据完全覆盖需求
                result['need_download'] = False
                result['missing_start'] = None
                result['missing_end'] = None
                print(f"[Tushare] 数据已覆盖：{ts_code}，本地范围 {local_start}-{local_end}")
            
            elif local_end < end_date:
                # 需要更新最新数据
                result['missing_start'] = (datetime.strptime(local_end, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
                result['missing_end'] = end_date
                print(f"[Tushare] 需要增量更新：{ts_code}，补充 {result['missing_start']}-{result['missing_end']}")
            
            elif local_start > start_date:
                # 需要补充早期数据（少见情况）
                result['missing_start'] = start_date
                result['missing_end'] = (datetime.strptime(local_start, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
                print(f"[Tushare] 需要补充早期数据：{ts_code}，补充 {result['missing_start']}-{result['missing_end']}")
            
            return result
            
        except Exception as e:
            print(f"[Tushare] 检查数据失败 {ts_code}: {e}")
            return result
    
    def get_or_download_data(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取数据（按需下载）
        
        策略：
        1. 先检查本地是否有数据
        2. 如果本地数据覆盖需求范围，直接返回
        3. 如果部分缺失，增量下载缺失部分
        4. 如果完全没有，下载整个范围
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
        
        Returns:
            数据 DataFrame
        """
        print(f"[Tushare] 按需获取数据：{ts_code}，范围 {start_date}-{end_date}")
        
        # 检查数据可用性
        availability = self.check_data_availability(ts_code, start_date, end_date)
        
        # 不需要下载，直接返回本地数据
        if not availability['need_download']:
            feature_file = self.features_dir / f"{ts_code.replace('.', '_')}.parquet"
            df = pd.read_parquet(feature_file)
            
            # 日期过滤
            df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
            
            print(f"[Tushare] 使用本地数据：{ts_code}，共 {len(df)} 条")
            return df
        
        # 需要下载
        download_start = availability['missing_start']
        download_end = availability['missing_end']
        
        # 获取数据（从 Tushare）
        new_df = self.get_daily_data(ts_code, download_start, download_end)
        
        if new_df.empty:
            print(f"[Tushare] 无新数据可下载：{ts_code}")
            # 返回现有数据（如果有）
            if availability['has_data']:
                feature_file = self.features_dir / f"{ts_code.replace('.', '_')}.parquet"
                df = pd.read_parquet(feature_file)
                return df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
            return pd.DataFrame()
        
        # 合并数据
        feature_file = self.features_dir / f"{ts_code.replace('.', '_')}.parquet"
        
        if feature_file.exists():
            existing_df = pd.read_parquet(feature_file)
            df = pd.concat([existing_df, new_df], ignore_index=True)
            df = df.drop_duplicates(subset=['trade_date'], keep='last')
        else:
            df = new_df
        
        # 排序并保存
        df = df.sort_values('trade_date')
        df.to_parquet(feature_file, index=False)
        
        print(f"[Tushare] 下载完成：{ts_code}，新增 {len(new_df)} 条，共 {len(df)} 条")
        
        # 返回请求范围的数据
        df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
        return df
    
    def get_data_summary(self) -> Dict:
        """获取数据摘要统计"""
        # 读取股票池
        if self.pool_file.exists():
            with open(self.pool_file, 'r', encoding='utf-8') as f:
                pool_config = yaml.safe_load(f)
            stock_count = len(pool_config.get('stocks', []))
        else:
            stock_count = 0
        
        # 统计特征文件
        feature_files = list(self.features_dir.glob("*.parquet"))
        total_records = 0
        
        for f in feature_files[:10]:  # 只统计前 10 个
            try:
                df = pd.read_parquet(f)
                total_records += len(df)
            except:
                pass
        
        return {
            'total_stocks': stock_count,
            'feature_files': len(feature_files),
            'total_records': total_records,
            'data_dir': str(self.base_dir),
            'last_updated': datetime.now().isoformat()
        }


# 全局服务实例
_tushare_service = None

def get_tushare_service(token: str = None) -> TushareService:
    """获取 Tushare 服务单例"""
    global _tushare_service
    if _tushare_service is None:
        _tushare_service = TushareService(token)
    return _tushare_service
