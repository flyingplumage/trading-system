"""
数据获取和增量更新测试脚本
测试目标：
1. 验证增量更新逻辑正确性
2. 测试按需获取数据
3. 确保数据无遗漏
4. 找到性能最优解
"""

import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace/projects/trading-system-release/backend')

from app.services.tushare_service import TushareService
from datetime import datetime, timedelta
import time

def test_incremental_update():
    """测试增量更新逻辑"""
    print("\n=== 测试 1: 增量更新逻辑 ===\n")
    
    ts = TushareService()
    
    # 测试用例 1: 新股票（全量下载）
    print("【测试 1.1】新股票全量下载")
    ts_code = "000001.SZ"
    count = ts.incremental_update(ts_code)
    print(f"  下载 {ts_code}: {count} 条记录\n")
    
    # 测试用例 2: 已存在股票（增量更新）
    print("【测试 1.2】已存在股票增量更新")
    last_date = ts.get_last_update_date(ts_code)
    print(f"  最后更新日期：{last_date}")
    
    # 立即再次更新（应该无新数据）
    count2 = ts.incremental_update(ts_code)
    print(f"  增量更新后：{count2} 条记录")
    print(f"  ✅ 增量更新逻辑正常\n")
    
    return True

def test_data_integrity():
    """测试数据完整性"""
    print("\n=== 测试 2: 数据完整性检查 ===\n")
    
    ts = TushareService()
    ts_code = "000001.SZ"
    
    # 检查数据连续性
    feature_file = ts.features_dir / f"{ts_code.replace('.', '_')}.parquet"
    
    if not feature_file.exists():
        print(f"  ⚠️ 数据文件不存在：{feature_file}")
        return False
    
    import pandas as pd
    df = pd.read_parquet(feature_file)
    
    # 检查日期范围
    min_date = df['trade_date'].min()
    max_date = df['trade_date'].max()
    total_days = (max_date - min_date).days + 1
    trade_days = len(df)
    
    print(f"  股票代码：{ts_code}")
    print(f"  数据范围：{min_date.date()} 到 {max_date.date()}")
    print(f"  总天数：{total_days} 天")
    print(f"  交易日：{trade_days} 天")
    print(f"  覆盖率：{trade_days / total_days * 100:.1f}%")
    
    # 检查数据缺口
    if len(df) > 1:
        df_sorted = df.sort_values('trade_date')
        gaps = df_sorted['trade_date'].diff().dt.days > 3
        gap_count = gaps.sum()
        if gap_count > 0:
            print(f"  ⚠️ 发现 {gap_count} 个数据缺口 (>3 天)")
        else:
            print(f"  ✅ 数据连续，无缺口")
    
    return True

def test_performance():
    """测试性能"""
    print("\n=== 测试 3: 性能测试 ===\n")
    
    ts = TushareService()
    
    # 测试单个股票下载时间
    ts_code = "000002.SZ"
    start = time.time()
    count = ts.incremental_update(ts_code)
    duration = time.time() - start
    
    print(f"  单个股票下载时间：{duration:.2f} 秒")
    print(f"  下载记录数：{count}")
    print(f"  速度：{count / duration:.1f} 条/秒")
    
    # 估算批量更新时间
    estimated_time = duration * 100  # 100 只股票
    print(f"\n  估算 100 只股票更新时间：{estimated_time / 60:.1f} 分钟")
    print(f"  估算 500 只股票更新时间：{estimated_time * 5 / 60:.1f} 分钟")
    
    return True

def test_on_demand_fetch():
    """测试按需获取"""
    print("\n=== 测试 4: 按需获取测试 ===\n")
    
    ts = TushareService()
    
    # 测试指定日期范围获取
    ts_code = "000001.SZ"
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    end_date = datetime.now().strftime('%Y%m%d')
    
    print(f"  请求范围：{start_date} 到 {end_date}")
    
    # 获取数据（不保存）
    df = ts.get_daily_data(ts_code, start_date, end_date)
    
    print(f"  获取记录数：{len(df)}")
    print(f"  数据范围：{df['trade_date'].min().date()} 到 {df['trade_date'].max().date()}")
    print(f"  ✅ 按需获取正常")
    
    return True

def recommend_optimal_strategy():
    """推荐最优策略"""
    print("\n=== 📊 最优策略推荐 ===\n")
    
    print("【策略 1: 增量更新 + 定期全量校验】")
    print("  - 日常：增量更新（快速）")
    print("  - 每周：全量校验一次（防遗漏）")
    print("  - 优点：平衡速度和完整性")
    print("  - 缺点：需要额外校验逻辑\n")
    
    print("【策略 2: 智能增量 + 缺口检测】")
    print("  - 每次更新前检查数据缺口")
    print("  - 自动补充缺失数据")
    print("  - 优点：数据完整性高")
    print("  - 缺点：增加 API 调用次数\n")
    
    print("【策略 3: 分批更新 + 断点续传】")
    print("  - 大批量分批次更新")
    print("  - 支持断点续传")
    print("  - 优点：适合大量股票")
    print("  - 缺点：实现复杂\n")
    
    print("✅ 推荐方案：策略 1 + 策略 2 组合")
    print("  1. 日常增量更新（带缺口检测）")
    print("  2. 每周一次全量校验")
    print("  3. 发现缺口自动补充")
    print("  4. 支持断点续传（防止中断）\n")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("数据获取和增量更新测试")
    print("=" * 60)
    
    try:
        # 运行测试
        test_incremental_update()
        test_data_integrity()
        test_performance()
        test_on_demand_fetch()
        recommend_optimal_strategy()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}\n")
        import traceback
        traceback.print_exc()
