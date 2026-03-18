"""SQLite 数据库管理 - 简单连接管理版"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "qframe.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# 初始化 WAL 模式（只需执行一次）
def _init_wal():
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=30.0)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    finally:
        conn.close()

# 初始化 WAL
_init_wal()


@contextmanager
def get_db_connection(read_only: bool = False):
    """
    获取数据库连接（简单连接管理）
    
    Args:
        read_only: 是否只读连接（目前未实现读写分离）
    
    Yields:
        sqlite3 连接对象
    """
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_transaction():
    """
    获取数据库事务上下文（自动提交/回滚）
    
    Yields:
        sqlite3 连接对象
    """
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 实验表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                strategy VARCHAR(128) NOT NULL,
                status VARCHAR(32) NOT NULL DEFAULT 'pending',
                config TEXT,
                metrics TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 模型表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                strategy VARCHAR(128) NOT NULL,
                version INTEGER NOT NULL,
                experiment_id VARCHAR(64),
                metrics TEXT,
                model_path VARCHAR(512),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 训练任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy VARCHAR(128) NOT NULL,
                steps INTEGER NOT NULL,
                status VARCHAR(32) DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                experiment_id VARCHAR(64),
                result TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        # 索引优化
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_strategy ON models(strategy)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON training_tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON training_tasks(priority)')


def create_experiment(exp_id: str, name: str, strategy: str, config: dict = None):
    """创建实验"""
    with get_db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO experiments (id, name, strategy, config)
            VALUES (?, ?, ?, ?)
        ''', (exp_id, name, strategy, json.dumps(config) if config else None))


def list_experiments(status: str = None, limit: int = 100):
    """获取实验列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute('SELECT * FROM experiments WHERE status = ? ORDER BY created_at DESC LIMIT ?', (status, limit))
        else:
            cursor.execute('SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def create_model(
    model_id: str,
    name: str,
    strategy: str,
    version: int,
    experiment_id: str = None,
    model_path: str = None,
    metrics: str = None
):
    """创建模型"""
    with get_db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO models (id, name, strategy, version, experiment_id, model_path, metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (model_id, name, strategy, version, experiment_id, model_path, metrics))


def list_models(strategy: str = None, limit: int = 100):
    """获取模型列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if strategy:
            cursor.execute('SELECT * FROM models WHERE strategy = ? ORDER BY created_at DESC LIMIT ?', (strategy, limit))
        else:
            cursor.execute('SELECT * FROM models ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def create_training_task(strategy: str, steps: int, priority: int = 5):
    """创建训练任务"""
    with get_db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO training_tasks (strategy, steps, priority)
            VALUES (?, ?, ?)
        ''', (strategy, steps, priority))
        return cursor.lastrowid


def get_pending_tasks():
    """获取待处理任务"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM training_tasks WHERE status = ? ORDER BY priority ASC, created_at ASC', ('pending',))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_training_task(task_id: int, status: str = None, result: str = None, error: str = None):
    """更新训练任务"""
    with get_db_transaction() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute('UPDATE training_tasks SET status = ? WHERE id = ?', (status, task_id))
        if result:
            cursor.execute('UPDATE training_tasks SET result = ? WHERE id = ?', (result, task_id))
        if error:
            cursor.execute('UPDATE training_tasks SET error = ? WHERE id = ?', (error, task_id))


def get_experiment(exp_id: str):
    """获取实验详情"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM experiments WHERE id = ?', (exp_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_experiment(exp_id: str, status: str = None, metrics: str = None, config: str = None):
    """更新实验"""
    with get_db_transaction() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute('UPDATE experiments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (status, exp_id))
        if metrics:
            cursor.execute('UPDATE experiments SET metrics = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (metrics, exp_id))
        if config:
            cursor.execute('UPDATE experiments SET config = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (config, exp_id))


def get_best_models(limit: int = 10):
    """获取最佳模型"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM models ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_training_task(task_id: int):
    """获取训练任务"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM training_tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_db_stats():
    """获取数据库统计"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM experiments')
        stats['experiments'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM models')
        stats['models'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM training_tasks')
        stats['training_tasks'] = cursor.fetchone()[0]
        
        return stats
