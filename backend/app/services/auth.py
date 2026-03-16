"""
JWT Token 管理
- Token 生成
- Token 验证
- 刷新机制
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path

# JWT 密钥 (生产环境应该从环境变量读取)
JWT_SECRET = secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: Dict, expires_minutes: int = TOKEN_EXPIRE_MINUTES) -> str:
    """创建访问 Token"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=expires_minutes)
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: Dict, expires_days: int = REFRESH_TOKEN_EXPIRE_DAYS) -> str:
    """创建刷新 Token"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=expires_days)
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[Dict]:
    """验证 Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # 检查 Token 类型
        token_type = payload.get("type")
        if token_type not in ["access", "refresh"]:
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """使用刷新 Token 获取新的访问 Token"""
    payload = verify_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        return None
    
    # 创建新的访问 Token
    return create_access_token({
        "user_id": payload["user_id"],
        "username": payload["username"],
        "role": payload["role"]
    })


# API Key 管理 (用于智能体/长期访问)
class APIKeyManager:
    """API Key 管理器"""
    
    def __init__(self, keys_file: str = "backend/data/api_keys.json"):
        self.keys_file = Path(keys_file)
        self.keys: Dict[str, Dict] = {}
        self.load_keys()
    
    def load_keys(self):
        """加载密钥"""
        if self.keys_file.exists():
            import json
            with open(self.keys_file, 'r', encoding='utf-8') as f:
                self.keys = json.load(f)
    
    def save_keys(self):
        """保存密钥"""
        self.keys_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(self.keys_file, 'w', encoding='utf-8') as f:
            json.dump(self.keys, f, indent=2, ensure_ascii=False)
    
    def generate_key(self, user_id: str, username: str, role: str = "user", 
                     expires_days: int = 365, name: str = None) -> str:
        """生成 API Key"""
        import secrets
        key = secrets.token_urlsafe(32)
        
        self.keys[key] = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "name": name or f"API Key {len(self.keys) + 1}",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=expires_days)).isoformat(),
            "last_used": None,
            "usage_count": 0,
            "is_active": True
        }
        
        self.save_keys()
        return key
    
    def verify_key(self, key: str) -> Optional[Dict]:
        """验证 API Key"""
        if key not in self.keys:
            return None
        
        key_info = self.keys[key]
        
        # 检查是否激活
        if not key_info.get("is_active", True):
            return None
        
        # 检查过期
        expires_at = datetime.fromisoformat(key_info["expires_at"])
        if datetime.now() > expires_at:
            return None
        
        # 更新使用记录
        key_info["last_used"] = datetime.now().isoformat()
        key_info["usage_count"] += 1
        self.save_keys()
        
        return {
            "user_id": key_info["user_id"],
            "username": key_info["username"],
            "role": key_info["role"]
        }
    
    def list_keys(self, username: str = None) -> list:
        """列出所有密钥"""
        keys = []
        for key, info in self.keys.items():
            if username and info["username"] != username:
                continue
            keys.append({
                "key_prefix": key[:8] + "...",  # 只显示前 8 位
                "name": info["name"],
                "username": info["username"],
                "role": info["role"],
                "created_at": info["created_at"],
                "expires_at": info["expires_at"],
                "last_used": info["last_used"],
                "usage_count": info["usage_count"],
                "is_active": info.get("is_active", True)
            })
        return keys
    
    def revoke_key(self, key: str) -> bool:
        """撤销密钥"""
        if key in self.keys:
            del self.keys[key]
            self.save_keys()
            return True
        return False
    
    def deactivate_key(self, key: str) -> bool:
        """停用密钥"""
        if key in self.keys:
            self.keys[key]["is_active"] = False
            self.save_keys()
            return True
        return False


# 全局 API Key 管理器
api_key_manager = APIKeyManager()


def get_api_key_manager() -> APIKeyManager:
    """获取 API Key 管理器"""
    return api_key_manager
