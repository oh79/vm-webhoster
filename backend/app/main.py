"""
VM 웹호스터 - FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.middleware import setup_all_middleware
from app.core.exception_handlers import setup_exception_handlers
from app.core.events import setup_event_handlers, start_background_tasks
from app.api.api import api_router
from app.utils.logging_utils import get_logger

# 로거 설정
logger = get_logger("main")

def create_application() -> FastAPI:
    """
    FastAPI 애플리케이션 생성 및 설정
    """
    # FastAPI 앱 인스턴스 생성
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs" if settings.DEBUG else None,  # 프로덕션에서는 docs 비활성화
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        # lifespan=lifespan  # FastAPI 0.93+ 방식
    )
    
    # 정적 파일 서빙 설정 (프론트엔드용)
    setup_static_files(app)
    
    # 미들웨어 설정
    setup_all_middleware(app)
    
    # 예외 핸들러 설정
    setup_exception_handlers(app)
    
    # 이벤트 핸들러 설정
    setup_event_handlers(app)
    
    # API 라우터 포함
    app.include_router(api_router, prefix="/api/v1")
    
    # 백그라운드 작업 시작
    # start_background_tasks()  # 필요시 활성화
    
    logger.info(f"{settings.PROJECT_NAME} 애플리케이션이 생성되었습니다.")
    return app

def setup_static_files(app: FastAPI):
    """
    정적 파일 서빙 설정
    """
    try:
        # 프론트엔드 빌드 파일 서빙
        frontend_path = Path("frontend/dist")
        if frontend_path.exists():
            app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
            logger.info("프론트엔드 정적 파일 서빙이 설정되었습니다.")
        
        # 업로드 파일 서빙 (VM 이미지 등)
        uploads_path = Path("uploads")
        uploads_path.mkdir(exist_ok=True)
        app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")
        
        # API 문서 관련 정적 파일
        if settings.DEBUG:
            docs_path = Path("docs")
            if docs_path.exists():
                app.mount("/docs-static", StaticFiles(directory=str(docs_path)), name="docs")
        
    except Exception as e:
        logger.warning(f"정적 파일 설정 중 오류: {e}")

# FastAPI 앱 인스턴스 생성
app = create_application()

# 루트 경로 핸들러
@app.get("/", include_in_schema=False)
async def root():
    """
    루트 경로 - 서비스 정보 반환
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "status": "running",
        "docs_url": "/docs" if settings.DEBUG else None,
        "api_prefix": "/api/v1"
    }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    파비콘 요청 처리 (404 방지)
    """
    from fastapi.responses import Response
    return Response(status_code=204)

# 헬스체크 엔드포인트들 (API 라우터 외부에 추가)
@app.get("/health", include_in_schema=False)
async def health_check():
    """서비스 상태 확인"""
    from datetime import datetime
    return {
        "status": "healthy", 
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ping", include_in_schema=False)
async def ping():
    """핑 테스트"""
    from datetime import datetime
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}

@app.get("/version", include_in_schema=False)
async def version():
    """버전 정보"""
    from app.schemas.common import StandardResponse
    from app.utils.response_utils import create_success_response
    
    return create_success_response(
        message="버전 정보를 조회했습니다.",
        data={
            "version": settings.VERSION,
            "service_name": settings.PROJECT_NAME,
            "description": settings.DESCRIPTION
        }
    )

@app.get("/health/detailed", include_in_schema=False)
async def detailed_health_check():
    """상세 헬스체크"""
    from datetime import datetime
    from sqlalchemy import text
    from app.db.session import get_db
    from app.schemas.common import StandardResponse
    from app.utils.response_utils import create_success_response
    
    try:
        # 데이터베이스 연결 확인
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_error = None
        db.close()
    except Exception as e:
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
    
    return create_success_response(
        message="서비스 상태가 정상입니다.",
        data=health_data
    )

# 개발 서버 실행 (직접 실행 시)
if __name__ == "__main__":
    import uvicorn
    
    logger.info("개발 서버를 시작합니다...")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST or "0.0.0.0",
        port=settings.PORT or 8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        workers=1 if settings.DEBUG else 4
    ) 