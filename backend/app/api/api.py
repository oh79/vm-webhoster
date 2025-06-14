"""
메인 API 라우터 - 모든 API 엔드포인트 통합
"""
from fastapi import APIRouter

from app.api.endpoints import (
    auth_router,
    users_router,
    hosting_router,
    health_router
)

# 메인 API 라우터 생성
api_router = APIRouter()

# 각 라우터를 메인 라우터에 포함
api_router.include_router(
    health_router,
    tags=["헬스체크"]
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["인증"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["사용자"]
)

# 호스팅은 단수형 /host 사용 (cursor_step.md 계획 따름)
api_router.include_router(
    hosting_router,
    prefix="/host",
    tags=["호스팅"]
) 