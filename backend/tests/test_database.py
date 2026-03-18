"""
数据库层测试
测试 database.py 中的各项功能
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import database


class TestDatabase:
    """数据库功能测试"""
    
    def test_init_db(self, test_db):
        """测试数据库初始化"""
        # 初始化应该创建所有表
        database.init_db()
        
        # 验证表存在
        cursor = test_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'experiments' in tables
        assert 'models' in tables
        assert 'training_tasks' in tables
    
    def test_create_experiment(self, test_db):
        """测试创建实验"""
        database.create_experiment(
            exp_id="exp_001",
            name="测试实验",
            strategy="test_strategy",
            config={"steps": 1000}
        )
        
        # 验证数据已写入
        cursor = test_db.cursor()
        cursor.execute("SELECT * FROM experiments WHERE id = ?", ("exp_001",))
        row = cursor.fetchone()
        
        assert row is not None
        assert row['name'] == "测试实验"
        assert row['strategy'] == "test_strategy"
    
    def test_get_experiment(self, test_db):
        """测试查询实验"""
        # 先创建
        database.create_experiment("exp_001", "Test", "strategy", {"lr": 0.01})
        
        # 再查询
        exp = database.get_experiment("exp_001")
        
        assert exp is not None
        assert exp['id'] == "exp_001"
        assert exp['name'] == "Test"
    
    def test_get_experiment_not_found(self, test_db):
        """测试查询不存在的实验"""
        exp = database.get_experiment("nonexistent")
        assert exp is None
    
    def test_list_experiments(self, test_db):
        """测试获取实验列表"""
        # 创建多个实验
        database.create_experiment("exp_001", "实验 1", "strategy_a", {})
        database.create_experiment("exp_002", "实验 2", "strategy_b", {})
        database.create_experiment("exp_003", "实验 3", "strategy_a", {})
        
        # 获取全部
        experiments = database.list_experiments(limit=10)
        assert len(experiments) == 3
        
        # 按状态筛选
        experiments = database.list_experiments(status="pending", limit=10)
        assert len(experiments) == 3  # 默认都是 pending
    
    def test_update_experiment(self, test_db):
        """测试更新实验"""
        database.create_experiment("exp_001", "Original", "strategy", {})
        
        # 更新状态
        database.update_experiment("exp_001", status="running")
        
        exp = database.get_experiment("exp_001")
        assert exp['status'] == "running"
    
    def test_create_model(self, test_db):
        """测试创建模型"""
        database.create_model(
            model_id="model_001",
            name="测试模型",
            strategy="test_strategy",
            version=1,
            experiment_id="exp_001",
            metrics='{"reward": 0.85}',
            model_path="/tmp/model.zip"
        )
        
        cursor = test_db.cursor()
        cursor.execute("SELECT * FROM models WHERE id = ?", ("model_001",))
        row = cursor.fetchone()
        
        assert row is not None
        assert row['name'] == "测试模型"
        assert row['version'] == 1
    
    def test_list_models(self, test_db):
        """测试获取模型列表"""
        database.create_model("m1", "模型 1", "strategy_a", 1)
        database.create_model("m2", "模型 2", "strategy_b", 1)
        database.create_model("m3", "模型 3", "strategy_a", 2)
        
        # 获取全部
        models = database.list_models(limit=10)
        assert len(models) == 3
        
        # 按策略筛选
        models = database.list_models(strategy="strategy_a", limit=10)
        assert len(models) == 2
    
    def test_create_training_task(self, test_db):
        """测试创建训练任务"""
        task_id = database.create_training_task(
            strategy="test_strategy",
            steps=10000,
            priority=5
        )
        
        assert task_id is not None
        assert task_id > 0
    
    def test_get_pending_tasks(self, test_db):
        """测试获取待处理任务"""
        database.create_training_task("strategy_a", 1000, priority=5)
        database.create_training_task("strategy_b", 2000, priority=3)
        database.create_training_task("strategy_c", 3000, priority=8)
        
        tasks = database.get_pending_tasks()
        
        assert len(tasks) == 3
        # 验证按优先级排序（数字越小优先级越高）
        assert tasks[0]['priority'] == 3
        assert tasks[1]['priority'] == 5
        assert tasks[2]['priority'] == 8
    
    def test_update_training_task(self, test_db):
        """测试更新训练任务"""
        task_id = database.create_training_task("strategy", 1000)
        
        # 更新状态
        database.update_training_task(task_id, status="running")
        
        task = database.get_training_task(task_id)
        assert task['status'] == "running"
    
    def test_get_db_stats(self, test_db):
        """测试获取数据库统计"""
        database.create_experiment("e1", "实验 1", "s1", {})
        database.create_experiment("e2", "实验 2", "s2", {})
        database.create_model("m1", "模型 1", "s1", 1)
        database.create_training_task("s1", 1000)
        
        stats = database.get_db_stats()
        
        assert stats['experiments'] == 2
        assert stats['models'] == 1
        assert stats['training_tasks'] == 1
    
    def test_transaction_rollback(self, test_db):
        """测试事务回滚（使用 get_db_transaction）"""
        # 这个测试验证异常时数据不会写入
        try:
            with database.get_db_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO experiments (id, name, strategy) VALUES (?, ?, ?)",
                    ("exp_rollback", "测试", "strategy")
                )
                # 故意抛出异常
                raise ValueError("模拟错误")
        except ValueError:
            pass
        
        # 验证数据已回滚
        exp = database.get_experiment("exp_rollback")
        assert exp is None


class TestConnectionPool:
    """连接池测试"""
    
    def test_get_connection(self):
        """测试获取连接"""
        with database.get_db_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_connection_auto_close(self):
        """测试连接自动关闭"""
        conn_id = None
        with database.get_db_connection() as conn:
            conn_id = id(conn)
        
        # 连接应该已关闭
        with pytest.raises(Exception):
            conn.cursor()
