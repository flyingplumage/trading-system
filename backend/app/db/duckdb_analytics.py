"""
DuckDB 分析数据库
用于存储和查询训练指标历史数据
"""

import duckdb
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / 'db' / 'trading.duckdb'


def get_connection():
    """获取 DuckDB 连接"""
    conn = duckdb.connect(str(DB_PATH))
    
    # 优化配置
    conn.execute("PRAGMA memory_limit='4GB'")
    
    return conn


def init_db():
    """初始化 DuckDB 表结构（仅实验分析数据）"""
    conn = get_connection()
    
    # 1. 实验指标表（核心表）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS experiment_metrics (
            id BIGINT PRIMARY KEY,
            experiment_id VARCHAR(64),
            step INTEGER,
            progress DOUBLE,
            reward DOUBLE,
            loss DOUBLE,
            portfolio_value DOUBLE,
            cash DOUBLE,
            position DOUBLE,
            sharpe_ratio DOUBLE,
            max_drawdown DOUBLE,
            win_rate DOUBLE,
            created_at TIMESTAMP
        )
    ''')
    
    # 2. 模型性能表（用于模型对比）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS model_performance (
            id BIGINT PRIMARY KEY,
            model_id VARCHAR(64),
            experiment_id VARCHAR(64),
            metric_name VARCHAR(64),
            metric_value DOUBLE,
            created_at TIMESTAMP
        )
    ''')
    
    # 3. 实验统计表（预聚合，加速查询）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS experiment_stats (
            experiment_id VARCHAR(64) PRIMARY KEY,
            total_steps INTEGER,
            final_progress DOUBLE,
            avg_reward DOUBLE,
            best_sharpe DOUBLE,
            min_drawdown DOUBLE,
            avg_win_rate DOUBLE,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds INTEGER,
            updated_at TIMESTAMP
        )
    ''')
    
    # 创建索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_exp ON experiment_metrics(experiment_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_step ON experiment_metrics(experiment_id, step)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_time ON experiment_metrics(created_at)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_model_exp ON model_performance(experiment_id)')
    
    conn.close()
    print("✅ DuckDB 初始化完成（实验分析库）")


def update_experiment_stats(exp_id: str):
    """
    更新实验统计表（预聚合）
    
    Args:
        exp_id: 实验 ID
    """
    conn = get_connection()
    
    conn.execute('''
        INSERT OR REPLACE INTO experiment_stats (
            experiment_id, total_steps, final_progress, avg_reward,
            best_sharpe, min_drawdown, avg_win_rate,
            start_time, end_time, duration_seconds, updated_at
        )
        SELECT 
            experiment_id,
            COUNT(*) as total_steps,
            MAX(progress) as final_progress,
            AVG(reward) as avg_reward,
            MAX(sharpe_ratio) as best_sharpe,
            MIN(max_drawdown) as min_drawdown,
            AVG(win_rate) as avg_win_rate,
            MIN(created_at) as start_time,
            MAX(created_at) as end_time,
            CAST(DATE_DIFF('second', MIN(created_at), MAX(created_at)) AS INTEGER) as duration_seconds,
            CURRENT_TIMESTAMP as updated_at
        FROM experiment_metrics
        WHERE experiment_id = ?
        GROUP BY experiment_id
    ''', [exp_id])
    
    conn.close()


def insert_metrics(metrics_list: list):
    """
    批量插入指标数据
    
    Args:
        metrics_list: 指标列表，每个元素是字典
    """
    conn = get_connection()
    
    # 转换为 DataFrame 批量插入（性能更好）
    import pandas as pd
    df = pd.DataFrame(metrics_list)
    
    # 确保 created_at 列存在
    if 'created_at' not in df.columns:
        from datetime import datetime
        df['created_at'] = datetime.now()
    
    # 只选择表结构中存在的列
    target_columns = [
        'id', 'experiment_id', 'step', 'progress', 'reward',
        'portfolio_value', 'cash', 'position'
    ]
    
    # 过滤 DataFrame 列
    df_filtered = df[[c for c in target_columns if c in df.columns]]
    
    # 添加默认值给缺失的列
    if 'sharpe_ratio' not in df_filtered.columns:
        df_filtered['sharpe_ratio'] = 0.0
    if 'max_drawdown' not in df_filtered.columns:
        df_filtered['max_drawdown'] = 0.0
    if 'win_rate' not in df_filtered.columns:
        df_filtered['win_rate'] = 0.0
    if 'created_at' not in df_filtered.columns:
        from datetime import datetime
        df_filtered['created_at'] = datetime.now()
    
    # 重新排列列顺序匹配表结构
    df_filtered = df_filtered[['id', 'experiment_id', 'step', 'progress', 'reward',
                                'portfolio_value', 'cash', 'position',
                                'sharpe_ratio', 'max_drawdown', 'win_rate', 'created_at']]
    
    # 使用显式列名插入（避免 OR REPLACE 的列数问题）
    conn.execute('''
        INSERT INTO experiment_metrics 
        (id, experiment_id, step, progress, reward, portfolio_value, 
         cash, position, sharpe_ratio, max_drawdown, win_rate, created_at)
        SELECT id, experiment_id, step, progress, reward, portfolio_value,
               cash, position, sharpe_ratio, max_drawdown, win_rate, created_at
        FROM df_filtered
    ''')
    
    # 更新实验统计
    if 'experiment_id' in df_filtered.columns:
        for exp_id in df_filtered['experiment_id'].unique():
            update_experiment_stats(exp_id)
    
    conn.close()
    print(f"✅ 插入 {len(metrics_list)} 条指标数据")


def get_metrics(exp_id: str, limit: int = 10000):
    """
    获取实验指标历史
    
    Args:
        exp_id: 实验 ID
        limit: 返回记录数限制
    """
    conn = get_connection()
    
    result = conn.execute('''
        SELECT step, progress, reward, portfolio_value, 
               sharpe_ratio, max_drawdown, win_rate, created_at
        FROM experiment_metrics
        WHERE experiment_id = ?
        ORDER BY step ASC
        LIMIT ?
    ''', [exp_id, limit]).fetchdf()
    
    conn.close()
    return result.to_dict('records')


def get_metrics_summary(exp_ids: list):
    """
    获取多个实验的统计摘要
    
    Args:
        exp_ids: 实验 ID 列表
    """
    conn = get_connection()
    
    placeholders = ','.join(['?' for _ in exp_ids])
    
    result = conn.execute(f'''
        SELECT 
            experiment_id,
            COUNT(*) as total_steps,
            MAX(progress) as final_progress,
            AVG(reward) as avg_reward,
            MAX(sharpe_ratio) as best_sharpe,
            MIN(max_drawdown) as min_drawdown,
            AVG(win_rate) as avg_win_rate,
            MIN(created_at) as start_time,
            MAX(created_at) as end_time
        FROM experiment_metrics
        WHERE experiment_id IN ({placeholders})
        GROUP BY experiment_id
    ''', exp_ids).fetchdf()
    
    conn.close()
    return result.to_dict('records')


def compare_experiments(exp_ids: list):
    """
    对比多个实验的关键指标
    
    Args:
        exp_ids: 实验 ID 列表
    """
    conn = get_connection()
    
    placeholders = ','.join(['?' for _ in exp_ids])
    
    result = conn.execute(f'''
        SELECT 
            experiment_id,
            -- 最终表现
            MAX(portfolio_value) as final_portfolio,
            MAX(sharpe_ratio) as best_sharpe,
            MIN(max_drawdown) as min_drawdown,
            
            -- 训练过程
            AVG(reward) as avg_reward,
            STDDEV(reward) as reward_std,
            MAX(win_rate) as best_win_rate,
            
            -- 效率
            COUNT(*) as total_steps,
            TIMESTAMPDIFF(SECOND, MIN(created_at), MAX(created_at)) as duration_seconds
        FROM experiment_metrics
        WHERE experiment_id IN ({placeholders})
        GROUP BY experiment_id
        ORDER BY best_sharpe DESC
    ''', exp_ids).fetchdf()
    
    conn.close()
    return result.to_dict('records')


def cleanup_old_metrics(days: int = 30):
    """
    清理指定天数前的指标数据
    
    Args:
        days: 保留最近 N 天的数据
    """
    conn = get_connection()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    result = conn.execute('''
        DELETE FROM experiment_metrics
        WHERE created_at < ?
    ''', [cutoff_date])
    
    deleted = result.rowcount
    conn.close()
    
    print(f"✅ 已清理 {deleted} 条 {days} 天前的指标数据")
    return deleted


def downsample_metrics(exp_id: str, sample_rate: int = 10):
    """
    对指标数据进行降采样
    
    Args:
        exp_id: 实验 ID
        sample_rate: 采样率（每 N 条保留 1 条）
    """
    conn = get_connection()
    
    # DuckDB 的窗口函数性能更好
    conn.execute('''
        DELETE FROM experiment_metrics
        WHERE experiment_id = ?
        AND id NOT IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (ORDER BY step) as rn
                FROM experiment_metrics
                WHERE experiment_id = ?
            ) WHERE rn = 1 OR rn % ? = 0
        )
    ''', [exp_id, exp_id, sample_rate])
    
    conn.close()
    print(f"✅ 实验 {exp_id} 降采样完成")


def get_database_size():
    """获取 DuckDB 文件大小（MB）"""
    db_path = Path(DB_PATH)
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        return size_mb
    return 0


def get_table_stats():
    """获取表统计信息"""
    conn = get_connection()
    
    result = conn.execute('''
        SELECT COUNT(*) as count FROM experiment_metrics
    ''').fetchone()
    
    conn.close()
    return {
        'experiment_metrics': result[0]
    }


def export_to_parquet(exp_id: str, output_path: str):
    """
    导出实验数据为 Parquet 格式（高压缩）
    
    Args:
        exp_id: 实验 ID
        output_path: 输出文件路径
    """
    conn = get_connection()
    
    conn.execute('''
        COPY (
            SELECT * FROM experiment_metrics
            WHERE experiment_id = ?
            ORDER BY step
        ) TO ? (FORMAT 'parquet', COMPRESSION 'zstd')
    ''', [exp_id, output_path])
    
    conn.close()
    print(f"✅ 已导出到 {output_path}")


if __name__ == '__main__':
    init_db()
    print(f"数据库大小：{get_database_size():.2f} MB")
