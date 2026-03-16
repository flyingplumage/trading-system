#!/usr/bin/env python3
"""
生成模拟股票数据（用于演示和测试）
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

def generate_mock_stock_data(
    stock_code: str,
    start_date: str = '2025-01-01',
    end_date: str = '2026-03-16',
    initial_price: float = 10.0
) -> pd.DataFrame:
    """
    生成模拟股票数据
    
    包含：
    - 开盘价、最高价、最低价、收盘价
    - 成交量、成交额
    """
    # 生成日期（排除周末）
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
    
    n_days = len(dates)
    print(f"生成 {stock_code} 的 {n_days} 天数据")
    
    # 生成价格（随机游走 + 趋势）
    np.random.seed(hash(stock_code) % 2**32)  # 固定随机种子
    
    # 趋势项（模拟上涨）
    trend = np.linspace(0, 0.5, n_days)
    
    # 随机波动
    returns = np.random.normal(0.001, 0.02, n_days)
    
    # 收盘价
    close = initial_price * (1 + trend + np.cumsum(returns) / 10)
    
    # 开盘价、最高价、最低价
    open_price = close * (1 + np.random.uniform(-0.01, 0.01, n_days))
    high = np.maximum(open_price, close) * (1 + np.random.uniform(0, 0.03, n_days))
    low = np.minimum(open_price, close) * (1 - np.random.uniform(0, 0.03, n_days))
    
    # 成交量（手）
    volume = np.random.uniform(10000, 100000, n_days)
    
    # 成交额（元）
    amount = volume * close * 100  # 1 手=100 股
    
    # 创建 DataFrame
    df = pd.DataFrame({
        'ts_code': [stock_code] * n_days,
        'trade_date': [d.strftime('%Y%m%d') for d in dates],
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'vol': volume,
        'amount': amount
    })
    
    return df


def main():
    """生成示例股票数据"""
    output_dir = Path(__file__).parent.parent / "shared" / "data" / "features"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 示例股票池
    stocks = [
        ('000001.SZ', 10.5),   # 平安银行
        ('000002.SZ', 25.0),   # 万科 A
        ('600519.SH', 1500.0), # 贵州茅台
        ('300750.SZ', 200.0),  # 宁德时代
        ('002594.SZ', 250.0),  # 比亚迪
    ]
    
    print("开始生成模拟数据...")
    
    for stock_code, initial_price in stocks:
        df = generate_mock_stock_data(stock_code, initial_price=initial_price)
        
        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        
        # 保存
        output_file = output_dir / f"{stock_code.replace('.', '_')}.parquet"
        df.to_parquet(output_file, index=False)
        
        print(f"✓ {stock_code}: {len(df)} 条记录 -> {output_file}")
    
    print(f"\n完成！共生成 {len(stocks)} 只股票数据")
    print(f"数据目录：{output_dir}")


if __name__ == '__main__':
    main()
