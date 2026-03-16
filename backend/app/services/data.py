"""
数据服务类
负责数据获取、处理和验证
支持按需从 Tushare 下载数据
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd

from .base import ServiceBase
from .exceptions import NotFoundError, ValidationError, InternalError


class DataService(ServiceBase):
    """数据服务类"""
    
    def __init__(self):
        super().__init__()
        self.data_dir = Path(__file__).parent.parent.parent / "shared" / "data"
        self.log_info("DataService 初始化")
    
    def list(self, **kwargs) -> List[Dict]:
        """
        获取数据文件列表
        
        Returns:
            数据文件列表
        """
        try:
            self.log_info("获取数据文件列表")
            
            data_files = []
            
            # 扫描数据目录
            for pattern in ['*.parquet', '*.csv']:
                for file in self.data_dir.rglob(pattern):
                    if file.is_file():
                        stat = file.stat()
                        data_files.append({
                            'path': str(file.relative_to(self.data_dir.parent.parent)),
                            'name': file.name,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'type': 'parquet' if file.suffix == '.parquet' else 'csv'
                        })
            
            self.log_info(f"找到 {len(data_files)} 个数据文件")
            return data_files
            
        except Exception as e:
            self.log_error("获取数据文件列表失败", e)
            raise InternalError("获取数据文件列表失败", e)
    
    def get(self, file_path: str) -> Dict:
        """
        获取数据文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件信息
        
        Raises:
            NotFoundError: 文件不存在
        """
        try:
            self.log_info("获取数据文件信息", file_path=file_path)
            
            full_path = self.data_dir.parent.parent / file_path
            
            if not full_path.exists():
                raise NotFoundError(f"数据文件不存在：{file_path}", "DATA_FILE")
            
            stat = full_path.stat()
            
            file_info = {
                'path': str(file_path),
                'name': full_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'parquet' if full_path.suffix == '.parquet' else 'csv'
            }
            
            self.log_info(f"获取文件信息成功：{file_path}")
            return file_info
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("获取数据文件信息失败", e, file_path=file_path)
            raise InternalError("获取数据文件信息失败", e)
    
    def create(self, data: Dict) -> Dict:
        """
        创建数据记录（元数据）
        
        Args:
            data: 数据元信息
        
        Returns:
            创建的数据记录
        """
        try:
            self.log_info("创建数据记录", name=data.get('name'))
            
            # 生成记录 ID
            record_id = f"data_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            record = {
                'id': record_id,
                'name': data.get('name', 'unknown'),
                'type': data.get('type', 'unknown'),
                'path': data.get('path'),
                'created_at': datetime.now().isoformat(),
                'metadata': data.get('metadata', {})
            }
            
            self.log_info(f"数据记录创建成功：{record_id}")
            return record
            
        except Exception as e:
            self.log_error("创建数据记录失败", e)
            raise InternalError("创建数据记录失败", e)
    
    def update(self, id: str, data: Dict) -> Dict:
        """
        更新数据记录
        
        Args:
            id: 记录 ID
            data: 更新数据
        
        Returns:
            更新后的记录
        """
        try:
            self.log_info("更新数据记录", id=id)
            
            # 这里只是示例，实际需要持久化存储
            updated = {
                'id': id,
                'updated_at': datetime.now().isoformat(),
                **data
            }
            
            self.log_info(f"数据记录更新成功：{id}")
            return updated
            
        except Exception as e:
            self.log_error("更新数据记录失败", e, id=id)
            raise InternalError("更新数据记录失败", e)
    
    def delete(self, id: str) -> bool:
        """
        删除数据记录
        
        Args:
            id: 记录 ID
        
        Returns:
            是否成功
        """
        try:
            self.log_info("删除数据记录", id=id)
            
            # 这里只是示例
            self.log_info(f"数据记录删除成功：{id}")
            return True
            
        except Exception as e:
            self.log_error("删除数据记录失败", e, id=id)
            raise InternalError("删除数据记录失败", e)
    
    def get_stock_list(self) -> List[str]:
        """
        获取股票池列表
        
        Returns:
            股票代码列表
        """
        try:
            pool_file = self.data_dir / "pool" / "stock_pool.yaml"
            
            if not pool_file.exists():
                self.log_warning("股票池文件不存在")
                return []
            
            import yaml
            with open(pool_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            stocks = config.get('stocks', [])
            self.log_info(f"获取到 {len(stocks)} 只股票")
            return stocks
            
        except Exception as e:
            self.log_error("获取股票列表失败", e)
            raise InternalError("获取股票列表失败", e)
    
    def get_price_data(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        auto_download: bool = True
    ) -> pd.DataFrame:
        """
        获取股票价格数据（支持按需下载）
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            auto_download: 是否自动从 Tushare 下载缺失数据
        
        Returns:
            价格数据 DataFrame
        """
        try:
            self.log_info("获取价格数据", stock_code=stock_code, auto_download=auto_download)
            
            features_dir = self.data_dir / "features"
            stock_file = features_dir / f"{stock_code.replace('.', '_')}.parquet"
            
            # 默认日期范围（最近 1 年）
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # 转换为 YYYYMMDD 格式（Tushare 格式）
            start_date_fmt = str(start_date).replace('-', '')
            end_date_fmt = str(end_date).replace('-', '')
            
            # 检查本地是否有数据
            if not stock_file.exists():
                if auto_download:
                    # 从 Tushare 下载
                    self.log_info("本地无数据，从 Tushare 下载", stock_code=stock_code)
                    from app.services.tushare_service import get_tushare_service
                    
                    try:
                        tushare = get_tushare_service()
                        df = tushare.get_or_download_data(
                            stock_code,
                            start_date_fmt,
                            end_date_fmt
                        )
                        
                        if df.empty:
                            raise NotFoundError(f"股票数据不存在且无法下载：{stock_code}", "STOCK_DATA")
                        
                        self.log_info(f"下载成功：{len(df)} 条记录")
                        return df
                        
                    except Exception as e:
                        self.log_error("Tushare 下载失败", e, stock_code=stock_code)
                        raise NotFoundError(f"股票数据不存在：{stock_code}", "STOCK_DATA")
                else:
                    raise NotFoundError(f"股票数据不存在：{stock_code}", "STOCK_DATA")
            
            # 读取本地数据
            df = pd.read_parquet(stock_file)
            
            # 检查是否需要更新（如果本地有数据但范围不够）
            if auto_download and not df.empty:
                if pd.api.types.is_datetime64_any_dtype(df['trade_date']):
                    local_end = df['trade_date'].max().strftime('%Y%m%d')
                else:
                    local_end = str(df['trade_date'].max())
                
                if local_end < end_date_fmt:
                    # 需要增量更新
                    self.log_info("本地数据过期，增量更新", stock_code=stock_code, local_end=local_end)
                    from app.services.tushare_service import get_tushare_service
                    
                    try:
                        tushare = get_tushare_service()
                        new_df = tushare.get_daily_data(stock_code, local_end, end_date_fmt)
                        
                        if not new_df.empty:
                            # 合并数据
                            df = pd.concat([df, new_df], ignore_index=True)
                            df = df.drop_duplicates(subset=['trade_date'], keep='last')
                            df = df.sort_values('trade_date')
                            
                            # 保存
                            df.to_parquet(stock_file, index=False)
                            self.log_info(f"增量更新成功：新增 {len(new_df)} 条")
                            
                    except Exception as e:
                        self.log_error("增量更新失败", e, stock_code=stock_code)
                        # 继续使用现有数据
            
            # 日期过滤
            if start_date:
                df = df[df['trade_date'] >= start_date]
            if end_date:
                df = df[df['trade_date'] <= end_date]
            
            self.log_info(f"获取到 {len(df)} 条记录")
            return df
            
        except NotFoundError:
            raise
        except Exception as e:
            self.log_error("获取价格数据失败", e, stock_code=stock_code)
            raise InternalError("获取价格数据失败", e)
    
    def get_data_summary(self) -> Dict:
        """获取数据摘要统计"""
        try:
            stock_list = self.get_stock_list()
            
            summary = {
                'total_stocks': len(stock_list),
                'data_dir': str(self.data_dir),
                'last_updated': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.log_error("获取数据摘要失败", e)
            raise InternalError("获取数据摘要失败", e)
