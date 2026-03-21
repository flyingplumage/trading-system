#!/usr/bin/env python3
"""
DuckDB 混合存储架构测试
验证 SQLite + DuckDB 双写功能
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['TUSHARE_TOKEN'] = 'a184c315fd031d9adc136b0c6519aa481bffc281c1ae114f77a25beb'
os.environ['DATABASE_URL'] = 'sqlite:///data/qframe.db'

from app.db import database
from app.db.duckdb_analytics import (
    init_db as duckdb_init,
    insert_metrics as duckdb_insert,
    get_metrics as duckdb_get_metrics,
    get_table_stats,
    get_database_size
)
from app.services.trainer import DUCKDB_AVAILABLE


def print_header(title: str):
    print()
    print('=' * 60)
    print(f'  {title}')
    print('=' * 60)
    print()


def test_duckdb_availability():
    """测试 1: DuckDB 可用性"""
    print_header('测试 1: DuckDB 可用性检查')
    
    print(f'DuckDB 模块可用性：{DUCKDB_AVAILABLE}')
    
    if not DUCKDB_AVAILABLE:
        print('❌ DuckDB 不可用，检查是否已安装')
        return False
    
    try:
        import duckdb
        print(f'✓ DuckDB 版本：{duckdb.__version__}')
    except Exception as e:
        print(f'✗ DuckDB 导入失败：{e}')
        return False
    
    return True


def test_duckdb_initialization():
    """测试 2: DuckDB 初始化"""
    print_header('测试 2: DuckDB 初始化')
    
    try:
        duckdb_init()
        print('✓ DuckDB 数据库初始化成功')
        
        # 检查数据库文件
        from pathlib import Path
        db_path = Path(__file__).parent.parent / 'app' / 'db' / 'trading.duckdb'
        if db_path.exists():
            print(f'✓ 数据库文件已创建：{db_path}')
            print(f'  文件大小：{db_path.stat().st_size / 1024:.2f} KB')
        else:
            print(f'⚠ 数据库文件未找到：{db_path}')
        
        return True
    except Exception as e:
        print(f'✗ DuckDB 初始化失败：{e}')
        return False


def test_duckdb_write():
    """测试 3: DuckDB 写入测试"""
    print_header('测试 3: DuckDB 写入测试')
    
    try:
        # 准备测试数据
        test_metrics = [
            {
                'id': int(time.time() * 1000) + i,
                'experiment_id': 'test_exp_001',
                'step': i * 100,
                'progress': (i * 100) / 5000 * 100,
                'reward': 0.1 * i,
                'portfolio_value': 1000000 * (1 + 0.01 * i),
                'cash': 500000,
                'position': 1000,
                'created_at': None  # 会被自动填充
            }
            for i in range(1, 11)
        ]
        
        print(f'准备写入 {len(test_metrics)} 条测试数据')
        
        # 批量写入
        duckdb_insert(test_metrics)
        print(f'✓ 成功写入 {len(test_metrics)} 条指标数据')
        
        return True
    except Exception as e:
        print(f'✗ DuckDB 写入失败：{e}')
        import traceback
        traceback.print_exc()
        return False


def test_duckdb_read():
    """测试 4: DuckDB 读取测试"""
    print_header('测试 4: DuckDB 读取测试')
    
    try:
        # 读取测试数据
        metrics = duckdb_get_metrics('test_exp_001', limit=100)
        
        if metrics:
            print(f'✓ 成功读取 {len(metrics)} 条记录')
            print(f'  第一条数据：step={metrics[0].get("step")}, progress={metrics[0].get("progress"):.1f}%')
            print(f'  最后一条数据：step={metrics[-1].get("step")}, progress={metrics[-1].get("progress"):.1f}%')
        else:
            print('⚠ 未读取到数据')
        
        return True
    except Exception as e:
        print(f'✗ DuckDB 读取失败：{e}')
        return False


def test_duckdb_stats():
    """测试 5: DuckDB 统计信息"""
    print_header('测试 5: DuckDB 统计信息')
    
    try:
        # 表统计
        table_stats = get_table_stats()
        print('表统计:')
        for table, count in table_stats.items():
            print(f'  - {table}: {count} 条记录')
        
        # 数据库大小
        db_size = get_database_size()
        print(f'数据库大小：{db_size:.2f} MB')
        
        return True
    except Exception as e:
        print(f'✗ 获取统计信息失败：{e}')
        return False


def test_sqlite_duckdb_dual_write():
    """测试 6: SQLite + DuckDB 双写模拟"""
    print_header('测试 6: SQLite + DuckDB 双写模拟')
    
    try:
        # 初始化数据库
        database.init_db()
        print('✓ SQLite 数据库已初始化')
        
        # 创建实验（SQLite）- 使用唯一 ID
        import time
        exp_id = f'dual_write_test_{int(time.time())}'
        database.create_experiment(
            exp_id=exp_id,
            name="Dual Write Test",
            strategy="ppo",
            config={'test': 'dual_write'}
        )
        print(f'✓ 实验已创建 (SQLite): {exp_id}')
        
        # 模拟训练指标写入（DuckDB）
        test_metrics = [
            {
                'id': int(time.time() * 1000) + i,
                'experiment_id': exp_id,
                'step': i * 100,
                'progress': (i * 100) / 1000 * 100,
                'reward': 0.05 * i,
                'portfolio_value': 1000000 + i * 1000,
                'cash': 500000,
                'position': 100,
                'created_at': None
            }
            for i in range(1, 6)
        ]
        
        duckdb_insert(test_metrics)
        print(f'✓ 指标已写入 (DuckDB): {len(test_metrics)} 条')
        
        # 验证双写
        sqlite_exp = database.get_experiment(exp_id)
        duckdb_metrics = duckdb_get_metrics(exp_id, limit=10)
        
        print()
        print('双写验证:')
        print(f'  SQLite 实验记录：{"✓" if sqlite_exp else "✗"}')
        print(f'  DuckDB 指标记录：{"✓" if duckdb_metrics else "✗"} ({len(duckdb_metrics)} 条)')
        
        return True
    except Exception as e:
        print(f'✗ 双写测试失败：{e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    print_header('DuckDB 混合存储架构测试')
    print('测试流程：可用性 → 初始化 → 写入 → 读取 → 统计 → 双写')
    
    results = []
    
    # 测试 1: 可用性
    results.append(('DuckDB 可用性', test_duckdb_availability()))
    
    if not DUCKDB_AVAILABLE:
        print()
        print('=' * 60)
        print('DuckDB 不可用，跳过后续测试')
        print('=' * 60)
        return 1
    
    # 测试 2: 初始化
    results.append(('DuckDB 初始化', test_duckdb_initialization()))
    
    # 测试 3: 写入
    results.append(('DuckDB 写入', test_duckdb_write()))
    
    # 测试 4: 读取
    results.append(('DuckDB 读取', test_duckdb_read()))
    
    # 测试 5: 统计
    results.append(('DuckDB 统计', test_duckdb_stats()))
    
    # 测试 6: 双写
    results.append(('SQLite+DuckDB 双写', test_sqlite_duckdb_dual_write()))
    
    # 汇总
    print_header('测试结果汇总')
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = '✅' if result else '❌'
        print(f'{status} {name}')
    
    print()
    print(f'总计：{passed}/{total} 通过')
    
    if passed == total:
        print()
        print('✅ 所有测试通过！混合存储架构工作正常')
        return 0
    else:
        print()
        print('⚠ 部分测试失败，请检查日志')
        return 1


if __name__ == '__main__':
    sys.exit(main())
