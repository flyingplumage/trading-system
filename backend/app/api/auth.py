"""
认证 API
- 用户注册/登录
- Token 管理
- API Key 管理
"""

from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import List, Optional
from app.schemas.schemas import Response
from app.services.users import user_manager, Role, ROLE_PERMISSIONS
from app.services.auth import (
    create_access_token, 
    create_refresh_token, 
    verify_token,
    refresh_access_token,
    api_key_manager
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])


# 请求/响应模型
class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "user"
    email: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class APIKeyCreate(BaseModel):
    name: Optional[str] = None
    role: str = "user"
    expires_days: int = 365


# 依赖项：验证 Token
async def get_current_user(authorization: Optional[str] = Header(None)):
    """获取当前用户 (从 JWT Token)"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息"
        )
    
    # 解析 Bearer Token
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证格式错误，应为：Bearer <token>"
        )
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期"
        )
    
    return {
        "user_id": payload["user_id"],
        "username": payload["username"],
        "role": payload["role"]
    }


# 依赖项：验证 API Key
async def get_current_user_from_apikey(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """获取当前用户 (从 API Key)"""
    if not x_api_key:
        return None
    
    payload = api_key_manager.verify_key(x_api_key)
    if not payload:
        return None
    
    return payload


# 依赖项：二选一认证
async def get_current_user_any(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """获取当前用户 (JWT 或 API Key)"""
    # 优先尝试 JWT
    if authorization:
        try:
            scheme, _, token = authorization.partition(" ")
            if scheme.lower() == "bearer":
                payload = verify_token(token)
                if payload:
                    return {
                        "user_id": payload["user_id"],
                        "username": payload["username"],
                        "role": payload["role"],
                        "auth_type": "jwt"
                    }
        except:
            pass
    
    # 尝试 API Key
    if x_api_key:
        payload = api_key_manager.verify_key(x_api_key)
        if payload:
            return {
                "user_id": payload["user_id"],
                "username": payload["username"],
                "role": payload["role"],
                "auth_type": "api_key"
            }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败，请提供有效的 Token 或 API Key"
    )


@router.post("/register", response_model=Response)
async def register(user_data: UserRegister):
    """用户注册"""
    # 检查用户名
    if len(user_data.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少 3 个字符")
    
    if len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 个字符")
    
    # 创建用户
    user = user_manager.create_user(
        username=user_data.username,
        password=user_data.password,
        role=user_data.role,
        email=user_data.email
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    return Response(
        success=True,
        message="注册成功",
        data=user
    )


@router.post("/login", response_model=Response)
async def login(credentials: UserLogin):
    """用户登录"""
    user = user_manager.authenticate(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成 Token
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    
    return Response(
        success=True,
        message="登录成功",
        data={
            **user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=Response)
async def refresh_token(request: RefreshTokenRequest):
    """刷新 Token"""
    new_access_token = refresh_access_token(request.refresh_token)
    
    if not new_access_token:
        raise HTTPException(status_code=401, detail="刷新 Token 无效或已过期")
    
    return Response(
        success=True,
        message="Token 已刷新",
        data={
            "access_token": new_access_token,
            "token_type": "Bearer"
        }
    )


@router.get("/me", response_model=Response)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    user_info = user_manager.get_user(current_user["username"])
    
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return Response(
        success=True,
        message="OK",
        data=user_info
    )


@router.get("/users", response_model=Response)
async def list_users(current_user: dict = Depends(get_current_user)):
    """列出所有用户 (需要管理员权限)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    users = user_manager.list_users()
    
    return Response(
        success=True,
        message="OK",
        data=users
    )


@router.post("/api-key/create", response_model=Response)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建 API Key"""
    key = api_key_manager.generate_key(
        user_id=current_user["user_id"],
        username=current_user["username"],
        role=key_data.role,
        expires_days=key_data.expires_days,
        name=key_data.name
    )
    
    return Response(
        success=True,
        message="API Key 已创建",
        data={
            "api_key": key,  # 只显示一次，请妥善保存
            "name": key_data.name,
            "role": key_data.role,
            "expires_days": key_data.expires_days
        }
    )


@router.get("/api-key/list", response_model=Response)
async def list_api_keys(
    current_user: dict = Depends(get_current_user)
):
    """列出 API Key"""
    keys = api_key_manager.list_keys(current_user["username"])
    
    return Response(
        success=True,
        message="OK",
        data=keys
    )


@router.post("/api-key/revoke/{key}", response_model=Response)
async def revoke_api_key(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """撤销 API Key"""
    success = api_key_manager.revoke_key(key)
    
    if not success:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    
    return Response(
        success=True,
        message="API Key 已撤销",
        data={"key_prefix": key[:8] + "..."}
    )


@router.get("/permissions", response_model=Response)
async def get_permissions(current_user: dict = Depends(get_current_user)):
    """获取当前用户权限"""
    from app.services.users import ROLE_PERMISSIONS
    
    role = current_user["role"]
    permissions = ROLE_PERMISSIONS.get(Role(role), {})
    
    return Response(
        success=True,
        message="OK",
        data={
            "username": current_user["username"],
            "role": role,
            "permissions": permissions
        }
    )
