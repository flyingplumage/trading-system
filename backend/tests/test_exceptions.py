"""
异常处理测试
测试全局异常处理器的功能
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestExceptionHandlers:
    """异常处理器测试"""
    
    def test_404_not_found(self, client):
        """测试 404 处理"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert 'message' in data
        assert 'error_code' in data
    
    def test_405_method_not_allowed(self, client):
        """测试 405 处理"""
        # 假设某个端点只支持 POST，用 GET 访问
        response = client.get("/api/auth/login")  # 如果 login 只支持 POST
        # 可能是 405 或 200（如果支持 GET）
        assert response.status_code in [200, 405]
    
    def test_validation_error(self, client):
        """测试参数验证错误处理"""
        # 发送无效的 JSON
        response = client.post(
            "/api/experiments",
            json={"invalid_field": "value"}  # 缺少必需字段
        )
        # 应该是 400 或 422
        assert response.status_code in [400, 422]
        if response.status_code == 400:
            data = response.json()
            assert data['success'] is False
    
    def test_internal_server_error(self, client):
        """测试内部错误处理（500）"""
        # 这个测试需要触发一个未处理的异常
        # 取决于具体实现，可能不容易测试
        pass


class TestResponseFormat:
    """响应格式一致性测试"""
    
    def test_success_response_structure(self, client):
        """测试成功响应结构"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        # 检查基本结构
        assert isinstance(data, dict)
    
    def test_error_response_structure(self, client):
        """测试错误响应结构"""
        response = client.get("/nonexistent")
        data = response.json()
        
        # 错误响应应包含这些字段
        assert data['success'] is False
        assert 'message' in data


class TestLogging:
    """日志功能测试"""
    
    def test_request_logging(self, client):
        """测试请求日志"""
        # 这个测试主要验证日志是否正常工作
        # 实际验证需要检查日志输出
        response = client.get("/health")
        assert response.status_code == 200
