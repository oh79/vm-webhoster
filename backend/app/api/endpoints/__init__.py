"""
API 엔드포인트 패키지 초기화
"""
from .auth import router as auth_router
from .users import router as users_router
from .hosting import router as hosting_router
from .health import router as health_router

__all__ = [
    "auth_router",
    "users_router", 
    "hosting_router",
    "health_router"
]
