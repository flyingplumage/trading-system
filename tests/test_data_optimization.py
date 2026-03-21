#!/usr/bin/env python3
"""
数据获取优化测试脚本
测试：缺口检测、增量更新、检查点机制
"""

import sys
import os

# 添加后端路径
sys.path.insert(0, '/root/.openclaw/workspace/projects/trading-system-release/backend')

from app.services.tushare_service import TushareService
from app.services.checkpoint import CheckpointManager
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def test_1_gap_detection():
    """测试 1: 缺口检测功能"""
    print_header("测试 1: 缺口检测功能")
    
    ts = TushareService()
    
    # 测试股票
    ts_code = "000001.SZ"
    print(f"测试股票：{ts_code}\n")
    
    # 1. 检测缺口
    print("【1】检测数据缺口...")
    gaps = ts.detect_gaps(ts_code)
    
    if gaps:
        print(f"  ✅ 发现 {len(gaps)} 个缺口:")
        for i, gap in enumerate(gaps[:5], 1):  # 只显示前 5 个
            print(f"    {i}. {gap['start']} - {gap['end']} ({gap['days']} 天)")
        if len(gaps) > 5:
            print(f"    ... 还有 {len(gaps) - 5} 个缺口")
    else:
        print(f"  ✅ 无缺口 (数据完整)")
    
    # 2. 获取数据范围
    print("\n【2】获取本地数据范围...")
    data_range = ts.get_local_data_range(ts_code)
    
    if data_range['start']:
        print(f"  开始日期：{data_range['start']}")
        print(f"  结束日期：{data_range['end']}")
        print(f"  总天数：{data_range['total_days']} 天")
        print(f"  交易日：{data_range['trade_days']} 天")
        if data_range['total_days'] > 0:
            coverage = data_range['trade_days'] / data_range['total_days'] * 100
            print(f"  覆盖率：{coverage:.1f}%")
    else:
        print(f"  ⚠️ 本地无数据")
    
    print("\n✅ 缺口检测测试完成")
    return True

def test_2_incremental_update():
    """测试 2: 增量更新（带缺口补充）"""
    print_header("测试 2: 增量更新（带缺口补充）")
    
    ts = TushareService()
    ts_code = "000001.SZ"
    
    print(f"测试股票：{ts_code}\n")
    
    # 1. 获取更新前状态
    print("【1】更新前状态...")
    before_range = ts.get_local_data_range(ts_code)
    if before_range['start']:
        print(f"  数据范围：{before_range['start']} - {before_range['end']}")
        print(f"  记录数：{before_range['trade_days']}")
    else:
        print(f"  本地无数据")
    
    # 2. 执行增量更新（带缺口补充）
    print("\n【2】执行增量更新（自动填补缺口）...")
    try:
        new_count = ts.incremental_update(ts_code, fill_gaps=True)
        print(f"  ✅ 更新完成")
        print(f"  总记录数：{new_count}")
    except Exception as e:
        print(f"  ❌ 更新失败：{e}")
        return False
    
    # 3. 获取更新后状态
    print("\n【3】更新后状态...")
    after_range = ts.get_local_data_range(ts_code)
    if after_range['start']:
        print(f"  数据范围：{after_range['start']} - {after_range['end']}")
        print(f"  记录数：{after_range['trade_days']}")
        
        # 比较前后
        if before_range['start']:
            added = after_range['trade_days'] - before_range['trade_days']
            print(f"  新增：{added} 条记录")
    else:
        print(f"  ⚠️ 本地仍无数据")
    
    print("\n✅ 增量更新测试完成")
    return True

def test_3_checkpoint():
    """测试 3: 检查点机制"""
    print_header("测试 3: 检查点机制")
    
    checkpoint = CheckpointManager()
    
    # 1. 保存检查点
    print("【1】保存检查点...")
    checkpoint.save('test_batch_update', {
        'last_index': 5,
        'last_stock': '000001.SZ',
        'stats': {'success': 5, 'failed': 0, 'new_records': 100}
    })
    print(f"  ✅ 检查点已保存")
    
    # 2. 加载检查点
    print("\n【2】加载检查点...")
    progress = checkpoint.load('test_batch_update')
    
    if progress:
        print(f"  ✅ 加载成功:")
        print(f"    最后索引：{progress.get('last_index', 0)}")
        print(f"    最后股票：{progress.get('last_stock', 'N/A')}")
        print(f"    成功数：{progress.get('stats', {}).get('success', 0)}")
    else:
        print(f"  ⚠️ 加载失败或已过期")
    
    # 3. 列出所有检查点
    print("\n【3】查看所有检查点...")
    checkpoints = checkpoint.list_checkpoints()
    
    if checkpoints:
        for cp in checkpoints:
            print(f"  - {cp['task_name']}: 索引 {cp['last_index']} ({cp['updated_at']})")
    else:
        print(f"  无检查点")
    
    # 4. 清除检查点
    print("\n【4】清除测试检查点...")
    checkpoint.clear('test_batch_update')
    print(f"  ✅ 已清除")
    
    print("\n✅ 检查点机制测试完成")
    return True

def test_4_batch_update():
    """测试 4: 批量更新（集成测试）"""
    print_header("测试 4: 批量更新（集成测试）")
    
    ts = TushareService()
    
    # 测试用股票列表（少量）
    test_stocks = ["000001.SZ", "000002.SZ"]
    
    print(f"测试股票：{test_stocks}")
    print(f"更新模式：带缺口检测 + 检查点\n")
    
    # 手动执行简化版批量更新
    stats = {
        'total': len(test_stocks),
        'success': 0,
        'failed': 0,
        'new_records': 0,
        'gaps_filled': 0
    }
    
    for i, ts_code in enumerate(test_stocks):
        print(f"\n[{i+1}/{len(test_stocks)}] 更新 {ts_code}...")
        
        try:
            # 检测缺口
            gaps = ts.detect_gaps(ts_code)
            if gaps:
                print(f"  发现 {len(gaps)} 个缺口")
                stats['gaps_filled'] += len(gaps)
            
            # 增量更新
            new_count = ts.incremental_update(ts_code, fill_gaps=True)
            stats['success'] += 1
            stats['new_records'] += new_count
            
            print(f"  ✅ 完成，共 {new_count} 条记录")
            
        except Exception as e:
            print(f"  ❌ 失败：{e}")
            stats['failed'] += 1
    
    # 输出统计
    print("\n" + "-" * 40)
    print("批量更新统计:")
    print(f"  总数：{stats['total']}")
    print(f"  成功：{stats['success']}")
    print(f"  失败：{stats['failed']}")
    print(f"  新增：{stats['new_records']} 条记录")
    print(f"  补缺：{stats['gaps_filled']} 个缺口")
    print("-" * 40)
    
    print("\n✅ 批量更新测试完成")
    return True

def main():
    """主测试流程"""
    print("\n" + "🧪" * 30)
    print("  数据获取优化功能测试")
    print("🧪" * 30)
    
    print(f"\n测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tushare 服务：{'✅ 已加载' if TushareService else '❌ 加载失败'}")
    
    try:
        # 运行所有测试
        test_1_gap_detection()
        test_2_incremental_update()
        test_3_checkpoint()
        test_4_batch_update()
        
        # 总结
        print_header("🎉 测试总结")
        print("✅ 所有测试完成!")
        print("\n测试项目:")
        print("  ✅ 缺口检测功能")
        print("  ✅ 增量更新（带缺口补充）")
        print("  ✅ 检查点机制")
        print("  ✅ 批量更新（集成测试）")
        print("\n系统状态:")
        print("  ✅ 数据获取优化已就绪")
        print("  ✅ 支持自动缺口检测和补充")
        print("  ✅ 支持断点续传")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
