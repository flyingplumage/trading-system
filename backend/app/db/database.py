"""SQLite 数据库管理 - 简化版"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "qframe.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
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
    
    conn.commit()
    conn.close()

def create_experiment(exp_id: str, name: str, strategy: str, config: dict = None):
    """创建实验"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO experiments (id, name, strategy, config)
        VALUES (?, ?, ?, ?)
    ''', (exp_id, name, strategy, json.dumps(config) if config else None))
    conn.commit()
    conn.close()

def list_experiments(status: str = None, limit: int = 100):
    """获取实验列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute('SELECT * FROM experiments WHERE status = ? ORDER BY created_at DESC LIMIT ?', (status, limit))
    else:
        cursor.execute('SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO models (id, name, strategy, version, experiment_id, model_path, metrics)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (model_id, name, strategy, version, experiment_id, model_path, metrics))
    conn.commit()
    conn.close()

def list_models(strategy: str = None, limit: int = 100):
    """获取模型列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if strategy:
        cursor.execute('SELECT * FROM models WHERE strategy = ? ORDER BY created_at DESC LIMIT ?', (strategy, limit))
    else:
        cursor.execute('SELECT * FROM models ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def create_training_task(strategy: str, steps: int, priority: int = 5):
    """创建训练任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO training_tasks (strategy, steps, priority)
        VALUES (?, ?, ?)
    ''', (strategy, steps, priority))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_pending_tasks():
    """获取待处理任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM training_tasks WHERE status = ? ORDER BY priority ASC, created_at ASC', ('pending',))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_training_task(task_id: int, status: str = None, result: str = None, error: str = None):
    """更新训练任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute('UPDATE training_tasks SET status = ? WHERE id = ?', (status, task_id))
    if result:
        cursor.execute('UPDATE training_tasks SET result = ? WHERE id = ?', (result, task_id))
    if error:
        cursor.execute('UPDATE training_tasks SET error = ? WHERE id = ?', (error, task_id))
    conn.commit()
    conn.close()

def get_experiment(exp_id: str):
    """获取实验详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM experiments WHERE id = ?', (exp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_experiment(exp_id: str, status: str = None, metrics: str = None, config: str = None):
    """更新实验"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute('UPDATE experiments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (status, exp_id))
    if metrics:
        cursor.execute('UPDATE experiments SET metrics = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (metrics, exp_id))
    if config:
        cursor.execute('UPDATE experiments SET config = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (config, exp_id))
    conn.commit()
    conn.close()

def get_best_models(limit: int = 10):
    """获取最佳模型"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM models ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_training_task(task_id: int):
    """获取训练任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM training_tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_db_stats():
    """获取数据库统计"""
    conn = get_db_connection()
    cursor = conn.cursor()
    stats = {}
    
    cursor.execute('SELECT COUNT(*) FROM experiments')
    stats['experiments'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM models')
    stats['models'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM training_tasks')
    stats['training_tasks'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# 自动初始化
init_db()
