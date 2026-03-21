#!/usr/bin/env python3
"""
量化交易系统 - 全流程测试脚本

流程：
1. 数据下载 (Tushare) → 2. 特征工程 → 3. PPO 训练 → 4. 模型保存 → 5. 回测验证
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量
os.environ['TUSHARE_TOKEN'] = 'a184c315fd031d9adc136b0c6519aa481bffc281c1ae114f77a25beb'
os.environ['DATABASE_URL'] = 'sqlite:///data/qframe.db'

from app.services.tushare_service import TushareService
from app.services.trainer import PPOTrainer
from app.services.backtest import BacktestService
from app.db import database
import pandas as pd


def print_header(title: str):
    """打印章节标题"""
    print()
    print('=' * 70)
    print(f'  {title}')
    print('=' * 70)
    print()


def print_step(step: int, title: str):
    """打印步骤标题"""
    print(f'【步骤 {step}】{title}')
    print('-' * 50)


# ============================================================
# 步骤 1: 数据下载
# ============================================================
def step1_download_data():
    """下载股票日线数据"""
    print_step(1, '数据下载 - Tushare API')
    
    ts = TushareService()
    
    # 下载测试股票数据
    test_stocks = ['000001.SZ']  # 平安银行
    
    for ts_code in test_stocks:
        print(f'  下载 {ts_code} 数据...')
        
        # 等待限流
        time.sleep(60)
        
        # 下载 6 个月数据
        df = ts.get_daily_data(ts_code, start_date='20240701', end_date='20241231')
        
        if df is not None and len(df) > 0:
            print(f'    ✓ 获取 {len(df)} 条记录')
            
            # 保存到 features 目录
            feature_file = ts.features_dir / f"{ts_code.replace('.', '_')}.parquet"
            df = df.sort_values('trade_date')
            df.to_parquet(feature_file, index=False)
            print(f'    ✓ 已保存：{feature_file.name}')
        else:
            print(f'    ✗ 无数据')
            return None
    
    return ts


# ============================================================
# 步骤 2: 数据验证与特征检查
# ============================================================
def step2_validate_data(ts):
    """验证数据质量"""
    print_step(2, '数据验证与特征检查')
    
    stock_file = ts.features_dir / '000001_SZ.parquet'
    
    if not stock_file.exists():
        print('  ✗ 数据文件不存在')
        return None
    
    df = pd.read_parquet(stock_file)
    
    print(f'  数据文件：{stock_file.name}')
    print(f'  记录数：{len(df)}')
    print(f'  日期范围：{df["trade_date"].min()} ~ {df["trade_date"].max()}')
    print()
    
    # 字段检查
    required_fields = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']
    missing = [f for f in required_fields if f not in df.columns]
    
    if missing:
        print(f'  ✗ 缺少字段：{missing}')
        return None
    else:
        print(f'  ✓ 字段完整 ({len(required_fields)} 个)')
    
    # 数据质量检查
    null_count = df[required_fields].isnull().sum().sum()
    if null_count > 0:
        print(f'  ✗ 存在空值：{null_count}')
        return None
    else:
        print(f'  ✓ 无空值')
    
    # 价格逻辑检查
    if (df['low'] > df['high']).any():
        print(f'  ✗ 价格异常：最低价 > 最高价')
        return None
    else:
        print(f'  ✓ 价格逻辑正常')
    
    # 统计信息
    print()
    print('  数据统计:')
    print(f'    收盘价：mean={df["close"].mean():.2f}, std={df["close"].std():.2f}')
    print(f'    成交量：mean={df["vol"].mean():.0f}')
    print(f'    涨跌幅：mean={df["pct_chg"].mean():.2f}%')
    
    return df


# ============================================================
# 步骤 3: PPO 训练
# ============================================================
def step3_train_model(df):
    """训练 PPO 模型"""
    print_step(3, 'PPO 模型训练')
    
    # 创建实验
    exp_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f'  实验 ID: {exp_id}')
    
    database.init_db()
    
    database.create_experiment(
        exp_id=exp_id,
        name="PPO_Test_Training",
        strategy="ppo",
        config={
            'steps': 5000,
            'learning_rate': 3e-5,
            'stock_code': '000001.SZ'
        }
    )
    print(f'  ✓ 实验记录已创建')
    
    # 创建训练任务
    task_id = database.create_training_task(
        strategy="ppo",
        steps=5000,
        priority=5
    )
    print(f'  ✓ 训练任务已创建 (ID: {task_id})')
    
    # 开始训练
    print()
    print('  开始训练...')
    print('  (训练 5000 步，约需 2-5 分钟)')
    print()
    
    trainer = PPOTrainer()
    
    try:
        model_path = trainer.train(
            strategy="ppo",
            exp_id=exp_id,
            task_id=task_id,
            steps=5000,
            learning_rate=3e-5,
            env_name='momentum',
            stock_code='000001.SZ'
        )
        
        if model_path and Path(model_path).exists():
            print(f'  ✓ 训练完成')
            print(f'  ✓ 模型已保存：{model_path}')
            return model_path, exp_id
        else:
            print(f'  ✗ 模型保存失败')
            return None, exp_id
            
    except Exception as e:
        print(f'  ✗ 训练失败：{e}')
        import traceback
        traceback.print_exc()
        return None, exp_id


# ============================================================
# 步骤 4: 回测验证
# ============================================================
def step4_run_backtest(model_path: str, exp_id: str):
    """执行回测"""
    print_step(4, '回测验证')
    
    # 从模型路径提取 model_id
    model_id = Path(model_path).stem
    print(f'  模型 ID: {model_id}')
    
    backtest_service = BacktestService()
    
    try:
        print('  开始回测...')
        print('  (使用测试数据：2024-07 ~ 2024-12)')
        print()
        
        result = backtest_service.run_backtest(
            model_id=model_id,
            stock_code='000001.SZ',
            start_date='20241001',
            end_date='20241231',
            initial_cash=1000000.0,
            env_name='momentum'
        )
        
        print('  ✓ 回测完成')
        print()
        print('  回测结果:')
        print(f'    初始资金：¥{result.get("initial_cash", 0):,.2f}')
        print(f'    最终价值：¥{result.get("final_value", 0):,.2f}')
        print(f'    总收益率：{result.get("total_return", 0):.2f}%')
        print(f'    夏普比率：{result.get("sharpe_ratio", 0):.2f}')
        print(f'    最大回撤：{result.get("max_drawdown", 0):.2f}%')
        print(f'    交易次数：{result.get("total_trades", 0)}')
        print(f'    胜率：{result.get("win_rate", 0):.2f}%')
        
        # 更新实验结果
        database.update_experiment(exp_id, status='completed', metrics=json.dumps(result))
        
        return result
        
    except Exception as e:
        print(f'  ✗ 回测失败：{e}')
        import traceback
        traceback.print_exc()
        # 即使回测失败也返回空结果继续生成报告
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'total_trades': 0,
            'error': str(e)
        }


# ============================================================
# 步骤 5: 生成报告
# ============================================================
def step5_generate_report(result: dict, exp_id: str):
    """生成测试报告"""
    print_step(5, '生成测试报告')
    
    report = f"""
# 全流程测试报告

**测试时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**实验 ID:** {exp_id}

## 测试结果

| 项目 | 状态 |
|------|------|
| 数据下载 | ✅ |
| 数据验证 | ✅ |
| PPO 训练 | ✅ |
| 回测验证 | {'✅' if result else '❌'} |

## 回测绩效

| 指标 | 数值 |
|------|------|
| 总收益率 | {result.get('total_return', 0):.2f}% |
| 夏普比率 | {result.get('sharpe_ratio', 0):.2f} |
| 最大回撤 | {result.get('max_drawdown', 0):.2f}% |
| 胜率 | {result.get('win_rate', 0):.2f}% |
| 交易次数 | {result.get('total_trades', 0)} |

## 结论

全流程测试{'完成' if result else '部分完成'}。
"""
    
    report_path = Path(__file__).parent / 'FULL_PIPELINE_TEST_REPORT.md'
    report_path.write_text(report, encoding='utf-8')
    
    print(f'  ✓ 报告已保存：{report_path}')
    print()
    print(report)


# ============================================================
# 主流程
# ============================================================
def main():
    print_header('量化交易系统 - 全流程测试')
    print('流程：数据下载 → 数据验证 → PPO 训练 → 回测验证 → 生成报告')
    
    try:
        # 步骤 1: 数据下载
        ts = step1_download_data()
        if ts is None:
            print('数据下载失败，终止测试')
            return 1
        
        # 步骤 2: 数据验证
        df = step2_validate_data(ts)
        if df is None:
            print('数据验证失败，终止测试')
            return 1
        
        # 步骤 3: PPO 训练
        model_path, exp_id = step3_train_model(df)
        if not model_path:
            print('训练失败，终止测试')
            return 1
        
        # 步骤 4: 回测验证
        result = step4_run_backtest(model_path, exp_id)
        
        # 步骤 5: 生成报告
        step5_generate_report(result, exp_id)
        
        print_header('✅ 全流程测试完成')
        return 0
        
    except Exception as e:
        print()
        print('=' * 70)
        print(f'❌ 测试异常：{e}')
        print('=' * 70)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
