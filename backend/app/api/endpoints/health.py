"""
헬스체크 및 서비스 상태 API 엔드포인트
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.schemas.common import StandardResponse, HealthCheck
from app.core.config import settings
from app.utils.response_utils import create_success_response
from app.utils.logging_utils import get_logger

# 라우터 설정
router = APIRouter(tags=["헬스체크"])
logger = get_logger("api.health")

@router.get(
    "/health",
    response_model=HealthCheck,
    summary="헬스체크",
    description="서비스 상태를 확인합니다."
)
def health_check():
    """
    기본 헬스체크
    
    서비스가 정상적으로 실행되고 있는지 확인합니다.
    """
    return HealthCheck(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.utcnow().isoformat()
    )

@router.get(
    "/health/detailed",
    response_model=StandardResponse[dict],
    summary="상세 헬스체크",
    description="데이터베이스 연결 상태를 포함한 상세 서비스 상태를 확인합니다."
)
def detailed_health_check(db: Session = Depends(get_db)):
    """
    상세 헬스체크
    
    데이터베이스 연결 상태와 기타 서비스 상태를 확인합니다.
    """
    try:
        # 데이터베이스 연결 확인
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_error = None
    except Exception as e:
        logger.error(f"데이터베이스 헬스체크 실패: {e}")
        db_status = "unhealthy"
        db_error = str(e)
    
    # 전체 상태 결정
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    
    health_data = {
        "service": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat()
        },
        "database": {
            "status": db_status,
            "error": db_error
        },
        "environment": {
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL
        }
    }
    
    # 상태에 따른 응답 코드 설정
    if overall_status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unhealthy"
        )
    
    return create_success_response(
        message="서비스 상태가 정상입니다.",
        data=health_data
    )

@router.get(
    "/version",
    response_model=StandardResponse[dict],
    summary="버전 정보",
    description="서비스 버전 및 구성 정보를 조회합니다."
)
def get_version():
    """
    버전 정보 조회
    
    서비스의 버전과 기본 구성 정보를 반환합니다.
    """
    version_data = {
        "service_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "environment": {
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL
        },
        "build_info": {
            "timestamp": datetime.utcnow().isoformat(),
            "python_version": "3.10+",
            "framework": "FastAPI"
        }
    }
    
    return create_success_response(
        message="버전 정보를 조회했습니다.",
        data=version_data
    )

@router.get(
    "/ping",
    summary="핑 테스트",
    description="간단한 응답 확인을 위한 핑 엔드포인트입니다."
)
def ping():
    """
    핑 테스트
    
    서비스 응답성을 확인하는 가장 간단한 엔드포인트입니다.
    """
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()} 