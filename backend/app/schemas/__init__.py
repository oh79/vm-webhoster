"""
Schemas 패키지 초기화
"""
from .common import (
    StandardResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    HealthCheck
)
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    Token,
    TokenData,
    LoginRequest,
    PasswordChange,
    AccountDeactivate
)
from .hosting import (
    HostingBase,
    HostingCreate,
    HostingUpdate,
    HostingResponse,
    HostingDetail,
    HostingStats,
    VMInfo,
    HostingOperation
)

__all__ = [
    # Common
    "StandardResponse",
    "ErrorResponse", 
    "PaginationParams",
    "PaginatedResponse",
    "HealthCheck",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "Token",
    "TokenData",
    "LoginRequest",
    "PasswordChange",
    "AccountDeactivate",
    # Hosting
    "HostingBase",
    "HostingCreate",
    "HostingUpdate",
    "HostingResponse",
    "HostingDetail",
    "HostingStats",
    "VMInfo",
    "HostingOperation"
]
