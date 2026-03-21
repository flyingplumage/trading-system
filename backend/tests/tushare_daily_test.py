#!/usr/bin/env python3
"""
Tushare 日线数据模块测试脚本
用于验证数据下载、保存、读取功能
"""

import os
import sys
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量
os.environ['TUSHARE_TOKEN'] = 'a184c315fd031d9adc136b0c6519aa481bffc281c1ae114f77a25beb'

from app.services.tushare_service import TushareService
import pandas as pd


def test_basic_connection():
    """测试基础连接"""
    print('[测试 1] 服务初始化...')
    ts = TushareService()
    assert ts.token, 'Token 未配置'
    assert ts.base_dir.exists(), '数据目录不存在'
    print('  ✓ 通过')
    return ts


def test_daily_data_fetch(ts):
    """测试日线数据获取"""
    print('[测试 2] 获取日线数据 (000001.SZ)...')
    df = ts.get_daily_data('000001.SZ', start_date='20241201', end_date='20241231')
    
    assert df is not None, '返回数据为空'
    assert len(df) > 0, '无数据记录'
    
    # 验证字段
    required_cols = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol']
    for col in required_cols:
        assert col in df.columns, f'缺少字段：{col}'
    
    # 验证数据质量
    assert (df['low'] <= df['high']).all(), '价格异常：最低价 > 最高价'
    assert df.isnull().sum().sum() == 0, '存在空值'
    
    print(f'  ✓ 通过 (获取 {len(df)} 条记录)')
    return df


def test_data_save(ts, df):
    """测试数据保存"""
    print('[测试 3] 保存数据...')
    ts_code = '000001.SZ'
    feature_file = ts.features_dir / f"{ts_code.replace('.', '_')}.parquet"
    
    df.to_parquet(feature_file, index=False)
    assert feature_file.exists(), '文件保存失败'
    
    size = feature_file.stat().st_size
    print(f'  ✓ 通过 (保存至 {feature_file.name}, {size} bytes)')
    return feature_file


def test_data_load(ts, feature_file):
    """测试数据读取"""
    print('[测试 4] 读取数据...')
    df = pd.read_parquet(feature_file)
    
    assert len(df) > 0, '读取数据为空'
    assert 'trade_date' in df.columns, '缺少日期字段'
    
    # 排序数据（确保按日期升序）
    df = df.sort_values('trade_date').reset_index(drop=True)
    
    # 验证日期已排序
    dates = pd.to_datetime(df['trade_date'])
    assert dates.is_monotonic_increasing, '日期未排序'
    
    print(f'  ✓ 通过 (读取 {len(df)} 条记录)')
    return df


def test_data_stats(df):
    """测试数据统计"""
    print('[测试 5] 数据统计分析...')
    
    stats = {
        '记录数': len(df),
        '日期范围': f"{df['trade_date'].min()} ~ {df['trade_date'].max()}",
        '收盘价范围': f"{df['close'].min():.2f} ~ {df['close'].max():.2f}",
        '平均成交量': f"{df['vol'].mean():.0f}",
        '平均涨跌幅': f"{df['pct_chg'].mean():.2f}%"
    }
    
    for k, v in stats.items():
        print(f'    {k}: {v}')
    
    print('  ✓ 通过')


def main():
    print('=' * 60)
    print('Tushare 日线数据模块 - 自动化测试')
    print('=' * 60)
    print()
    
    try:
        # 执行测试
        ts = test_basic_connection()
        
        print()
        df = test_daily_data_fetch(ts)
        
        print()
        feature_file = test_data_save(ts, df)
        
        print()
        df = test_data_load(ts, feature_file)
        
        print()
        test_data_stats(df)
        
        print()
        print('=' * 60)
        print('✅ 所有测试通过！')
        print('=' * 60)
        return 0
        
    except AssertionError as e:
        print()
        print('=' * 60)
        print(f'❌ 测试失败：{e}')
        print('=' * 60)
        return 1
    except Exception as e:
        print()
        print('=' * 60)
        print(f'❌ 异常：{e}')
        print('=' * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
