"""
웹 호스팅 서비스 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="웹 호스팅 서비스 API",
    description="자동화된 VM 기반 웹 호스팅 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정 (Nginx에서 주요 CORS 처리, 여기서는 기본 설정만)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Nginx에서 제한하므로 여기서는 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 포함
app.include_router(api_router, prefix="/api/v1")

# Health check 엔드포인트
@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "웹 호스팅 서비스"}

# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트"""
    print("🚀 웹 호스팅 서비스가 시작되었습니다!")

# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    print("👋 웹 호스팅 서비스가 종료됩니다.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 