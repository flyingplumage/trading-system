"""
权限检查依赖项
用于保护 API 端点
"""

from fastapi import HTTPException, status
from typing import List, Callable
from app.services.users import Role, ROLE_PERMISSIONS


def check_permission(resource: str, action: str):
    """
    权限检查装饰器
    
    用法:
    @router.get("/protected")
    async def protected_endpoint(current_user: dict = Depends(check_permission("train", "create"))):
        ...
    """
    async def permission_checker(current_user: dict):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证"
            )
        
        role = Role(current_user.get("role", "user"))
        permissions = ROLE_PERMISSIONS.get(role, {})
        
        resource_perms = permissions.get(resource, [])
        if action not in resource_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {resource}:{action}"
            )
        
        return current_user
    
    return permission_checker


# 预定义的权限检查函数
require_train_create = check_permission("train", "create")
require_train_read = check_permission("train", "read")
require_train_update = check_permission("train", "update")
require_train_delete = check_permission("train", "delete")

require_backtest_create = check_permission("backtest", "create")
require_backtest_read = check_permission("backtest", "read")

require_model_create = check_permission("model", "create")
require_model_read = check_permission("model", "read")

require_data_read = check_permission("data", "read")
require_data_update = check_permission("data", "update")

require_queue_config = check_permission("queue", "config")

require_user_read = check_permission("user", "read")
require_user_admin = check_permission("user", "delete")  # 管理员权限
