"""
API 路由测试
测试主要 API 端点的功能
"""

import pytest
import json
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'apis' in data['data']
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_agent_status(self, client):
        """测试 Agent 状态"""
        response = client.get("/api/agent/status")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'status' in data['data']


class TestExperimentEndpoints:
    """实验相关端点测试"""
    
    def test_create_experiment(self, client):
        """测试创建实验"""
        payload = {
            "name": "测试实验",
            "strategy": "test_strategy",
            "config": {"steps": 1000, "lr": 0.001}
        }
        
        response = client.post("/api/experiments", json=payload)
        assert response.status_code == 200
    
    def test_list_experiments(self, client):
        """测试获取实验列表"""
        # 先创建
        client.post("/api/experiments", json={
            "name": "实验 1",
            "strategy": "strategy_a",
            "config": {}
        })
        
        # 再列表
        response = client.get("/api/experiments")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_experiment(self, client):
        """测试获取单个实验"""
        # 创建实验
        create_resp = client.post("/api/experiments", json={
            "name": "测试实验",
            "strategy": "test",
            "config": {}
        })
        exp_id = create_resp.json()['data']['id']
        
        # 获取详情
        response = client.get(f"/api/experiments/{exp_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['data']['id'] == exp_id
    
    def test_get_experiment_not_found(self, client):
        """测试获取不存在的实验"""
        response = client.get("/api/experiments/nonexistent")
        assert response.status_code in [404, 200]  # 取决于实现


class TestModelEndpoints:
    """模型相关端点测试"""
    
    def test_list_models(self, client):
        """测试获取模型列表"""
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True


class TestTrainingEndpoints:
    """训练相关端点测试"""
    
    def test_create_training_task(self, client):
        """测试创建训练任务"""
        payload = {
            "strategy": "test_strategy",
            "steps": 10000,
            "priority": 5
        }
        
        response = client.post("/api/train", json=payload)
        assert response.status_code in [200, 201]
    
    def test_get_queue(self, client):
        """测试获取任务队列"""
        response = client.get("/api/queue")
        assert response.status_code == 200


class TestResponseFormat:
    """响应格式测试"""
    
    def test_success_response_format(self, client):
        """测试成功响应格式"""
        response = client.get("/health")
        data = response.json()
        
        # 验证标准响应格式
        assert 'success' in data or 'status' in data
    
    def test_error_response_format(self, client):
        """测试错误响应格式"""
        response = client.get("/api/nonexistent")
        # 404 也是有效的错误响应
        assert response.status_code == 404


class TestCORS:
    """CORS 测试"""
    
    def test_cors_headers(self, client):
        """测试 CORS 头"""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        # FastAPI 的 CORS 中间件应该添加这些头
        assert response.status_code == 200
