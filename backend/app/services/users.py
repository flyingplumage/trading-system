"""
用户管理系统
- 用户注册/登录
- 用户信息管理
- 角色权限
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from enum import Enum


class Role(Enum):
    """用户角色"""
    ADMIN = "admin"          # 管理员 - 所有权限
    DEVELOPER = "developer"  # 开发者 - 训练/回测/数据
    USER = "user"            # 普通用户 - 只读/有限训练
    BOT = "bot"              # 机器人 (OpenClaw 智能体) - API 访问


# 角色权限映射
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        "train": ["create", "read", "update", "delete"],
        "backtest": ["create", "read", "update", "delete"],
        "model": ["create", "read", "update", "delete"],
        "data": ["create", "read", "update", "delete"],
        "user": ["create", "read", "update", "delete"],
        "queue": ["create", "read", "update", "delete", "config"],
    },
    Role.DEVELOPER: {
        "train": ["create", "read", "update"],
        "backtest": ["create", "read", "update"],
        "model": ["create", "read", "update"],
        "data": ["create", "read", "update"],
        "user": ["read"],
        "queue": ["create", "read", "update"],
    },
    Role.USER: {
        "train": ["read"],
        "backtest": ["read"],
        "model": ["read"],
        "data": ["read"],
        "user": [],
        "queue": ["read"],
    },
    Role.BOT: {
        "train": ["create", "read", "update"],
        "backtest": ["create", "read"],
        "model": ["read"],
        "data": ["read", "update"],
        "user": [],
        "queue": ["create", "read", "config"],
    },
}


class UserManager:
    """用户管理器"""
    
    def __init__(self, users_file: str = "backend/data/users.json"):
        self.users_file = Path(users_file)
        self.users: Dict[str, Dict] = {}
        self.load_users()
    
    def load_users(self):
        """加载用户"""
        if self.users_file.exists():
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
    
    def save_users(self):
        """保存用户"""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=2, ensure_ascii=False)
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(
        self,
        username: str,
        password: str,
        role: str = "user",
        email: str = None
    ) -> Optional[Dict]:
        """创建用户"""
        # 检查用户名是否存在
        if username in self.users:
            return None
        
        user_id = f"user_{secrets.token_hex(8)}"
        
        self.users[username] = {
            "user_id": user_id,
            "username": username,
            "password_hash": self._hash_password(password),
            "role": role,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }
        
        self.save_users()
        
        return {
            "user_id": user_id,
            "username": username,
            "role": role
        }
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """用户认证"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        
        # 检查密码
        if user["password_hash"] != self._hash_password(password):
            return None
        
        # 检查是否激活
        if not user.get("is_active", True):
            return None
        
        # 更新最后登录时间
        user["last_login"] = datetime.now().isoformat()
        self.save_users()
        
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }
    
    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "email": user.get("email"),
            "created_at": user["created_at"],
            "last_login": user.get("last_login"),
            "is_active": user.get("is_active", True)
        }
    
    def update_user(self, username: str, data: Dict) -> bool:
        """更新用户信息"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        # 允许更新的字段
        allowed_fields = ["email", "role", "is_active"]
        for field in allowed_fields:
            if field in data:
                user[field] = data[field]
        
        # 密码更新
        if "password" in data:
            user["password_hash"] = self._hash_password(data["password"])
        
        self.save_users()
        return True
    
    def delete_user(self, username: str) -> bool:
        """删除用户"""
        if username in self.users:
            del self.users[username]
            self.save_users()
            return True
        return False
    
    def list_users(self) -> List[Dict]:
        """列出所有用户"""
        return [
            {
                "user_id": u["user_id"],
                "username": u["username"],
                "role": u["role"],
                "email": u.get("email"),
                "created_at": u["created_at"],
                "last_login": u.get("last_login"),
                "is_active": u.get("is_active", True)
            }
            for u in self.users.values()
        ]
    
    def check_permission(self, username: str, resource: str, action: str) -> bool:
        """检查权限"""
        if username not in self.users:
            return False
        
        role = Role(self.users[username]["role"])
        permissions = ROLE_PERMISSIONS.get(role, {})
        
        resource_perms = permissions.get(resource, [])
        return action in resource_perms


# 全局用户管理器
user_manager = UserManager()


def get_user_manager() -> UserManager:
    """获取用户管理器"""
    return user_manager
