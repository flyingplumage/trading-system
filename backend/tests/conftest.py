"""
测试夹具（Fixtures）
提供通用的测试资源和配置
"""

import pytest
import sqlite3
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.db import database


# 测试数据库路径
TEST_DB_PATH = Path(__file__).parent / "test.db"


@pytest.fixture(scope="function")
def test_db() -> Generator[sqlite3.Connection, None, None]:
    """
    创建测试数据库（每个测试函数独立）
    """
    # 使用内存数据库或临时文件
    conn = sqlite3.connect(str(TEST_DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # 初始化表结构
    database.init_db()
    
    yield conn
    
    # 清理
    conn.close()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    创建测试客户端
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_experiment_data() -> dict:
    """
    测试实验数据
    """
    return {
        "id": "test_exp_001",
        "name": "测试实验",
        "strategy": "test_strategy",
        "config": {"steps": 1000, "lr": 0.001}
    }


@pytest.fixture
def test_model_data() -> dict:
    """
    测试模型数据
    """
    return {
        "id": "test_model_001",
        "name": "测试模型",
        "strategy": "test_strategy",
        "version": 1,
        "experiment_id": "test_exp_001",
        "metrics": {"reward": 0.85, "steps": 1000},
        "model_path": "/tmp/test_model.zip",
        "model_hash": "abc123"
    }


@pytest.fixture
def test_training_task_data() -> dict:
    """
    测试训练任务数据
    """
    return {
        "strategy": "test_strategy",
        "steps": 10000,
        "priority": 5
    }


# 自动清理测试数据库
@pytest.fixture(autouse=True)
def cleanup():
    """
    每个测试前后清理
    """
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
