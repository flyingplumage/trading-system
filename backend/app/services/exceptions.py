"""
服务层自定义异常
"""


class ServiceError(Exception):
    """服务层基础异常"""
    
    def __init__(self, message: str, code: str = "SERVICE_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "status_code": self.status_code
        }


class NotFoundError(ServiceError):
    """资源未找到异常"""
    
    def __init__(self, message: str = "资源未找到", resource_type: str = None):
        code = "NOT_FOUND"
        if resource_type:
            code = f"{resource_type.upper()}_NOT_FOUND"
        super().__init__(message, code, status_code=404)


class ValidationError(ServiceError):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None):
        code = "VALIDATION_ERROR"
        if field:
            message = f"字段 '{field}': {message}"
        super().__init__(message, code, status_code=400)


class ConflictError(ServiceError):
    """资源冲突异常"""
    
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, "CONFLICT_ERROR", status_code=409)


class InternalError(ServiceError):
    """内部服务异常"""
    
    def __init__(self, message: str = "内部服务错误", original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message, "INTERNAL_ERROR", status_code=500)


class PermissionError(ServiceError):
    """权限异常"""
    
    def __init__(self, message: str = "无权限访问"):
        super().__init__(message, "PERMISSION_ERROR", status_code=403)
