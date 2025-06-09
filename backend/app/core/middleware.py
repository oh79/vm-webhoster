"""
FastAPI 미들웨어 설정
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.utils.logging_utils import get_logger, log_request_info, log_performance

logger = get_logger("middleware")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    API 요청 로깅 미들웨어
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 요청 시작 시간
        start_time = time.time()
        
        # 요청 정보 로깅
        log_request_info(
            method=request.method,
            url=str(request.url),
            extra_info={
                "request_id": request_id,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        try:
            # 요청 처리
            response = await call_next(request)
            
            # 처리 시간 계산
            process_time = (time.time() - start_time) * 1000
            
            # 성능 로깅
            log_performance(
                operation=f"{request.method} {request.url.path}",
                duration_ms=process_time,
                success=response.status_code < 400,
                extra_info={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            # 응답 헤더에 요청 ID 추가
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            return response
            
        except Exception as e:
            # 에러 처리 시간 계산
            process_time = (time.time() - start_time) * 1000
            
            # 에러 로깅
            logger.error(
                f"요청 처리 중 오류 발생: {type(e).__name__}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "process_time": f"{process_time:.2f}ms"
                }
            )
            
            # 에러 응답 반환
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "내부 서버 오류가 발생했습니다.",
                    "data": None,
                    "request_id": request_id
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": f"{process_time:.2f}ms"
                }
            )

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    보안 헤더 추가 미들웨어
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 보안 헤더 추가
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        })
        
        # HTTPS 강제 (프로덕션 환경에서)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    간단한 요청 제한 미들웨어 (메모리 기반)
    프로덕션에서는 Redis 등을 사용하는 것이 좋습니다.
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 허용 요청 수
        self.period = period  # 시간 주기 (초)
        self.clients = {}  # 클라이언트별 요청 기록
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 클라이언트 IP 가져오기
        client_ip = request.client.host if request.client else "unknown"
        
        # 현재 시간
        now = time.time()
        
        # 클라이언트 요청 기록 정리 (오래된 기록 삭제)
        if client_ip in self.clients:
            self.clients[client_ip] = [
                timestamp for timestamp in self.clients[client_ip]
                if now - timestamp < self.period
            ]
        else:
            self.clients[client_ip] = []
        
        # 요청 수 확인
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning(f"Rate limit exceeded for client {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": f"요청 한도를 초과했습니다. {self.period}초 후 다시 시도해주세요.",
                    "data": None
                },
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.period))
                }
            )
        
        # 요청 기록 추가
        self.clients[client_ip].append(now)
        
        # 요청 처리
        response = await call_next(request)
        
        # 레이트 리미트 헤더 추가
        remaining = max(0, self.calls - len(self.clients[client_ip]))
        response.headers.update({
            "X-RateLimit-Limit": str(self.calls),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(now + self.period))
        })
        
        return response

def setup_cors_middleware(app):
    """
    CORS 미들웨어 설정
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "X-Request-ID"
        ],
        expose_headers=[
            "X-Request-ID",
            "X-Process-Time",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
    )

def setup_trusted_host_middleware(app):
    """
    신뢰할 수 있는 호스트 미들웨어 설정
    """
    if not settings.DEBUG and settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )

def setup_custom_middleware(app):
    """
    커스텀 미들웨어 설정
    """
    # 보안 헤더 미들웨어
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 요청 로깅 미들웨어
    app.add_middleware(RequestLoggingMiddleware)
    
    # 레이트 리미트 미들웨어 (개발 환경에서는 비활성화)
    if not settings.DEBUG:
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.RATE_LIMIT_CALLS or 100,
            period=settings.RATE_LIMIT_PERIOD or 60
        )

def setup_all_middleware(app):
    """
    모든 미들웨어 설정
    """
    # 순서가 중요합니다 (LIFO - Last In, First Out)
    
    # 1. 커스텀 미들웨어 (가장 나중에 실행)
    setup_custom_middleware(app)
    
    # 2. CORS 미들웨어
    setup_cors_middleware(app)
    
    # 3. 신뢰할 수 있는 호스트 미들웨어 (가장 먼저 실행)
    setup_trusted_host_middleware(app)
    
    logger.info("모든 미들웨어가 설정되었습니다.") 