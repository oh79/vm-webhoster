"""
FastAPI 전역 예외 핸들러
"""
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    WebHostingException,
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InsufficientPermissionError,
    HostingNotFoundError,
    HostingAlreadyExistsError,
    VMOperationError
)
from app.utils.logging_utils import get_logger, log_error_with_context

logger = get_logger("exception_handlers")

def create_error_response(
    request: Request,
    status_code: int,
    message: str,
    detail: str = None,
    error_code: str = None
) -> JSONResponse:
    """
    표준 에러 응답 생성
    """
    # 요청 ID 가져오기 (미들웨어에서 설정됨)
    request_id = getattr(request.state, 'request_id', None)
    
    content = {
        "success": False,
        "message": message,
        "data": None
    }
    
    if detail:
        content["detail"] = detail
    
    if error_code:
        content["error_code"] = error_code
    
    if request_id:
        content["request_id"] = request_id
    
    headers = {}
    if request_id:
        headers["X-Request-ID"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers
    )

async def custom_exception_handler(
    request: Request, 
    exc: WebHostingException
) -> JSONResponse:
    """
    커스텀 예외 핸들러
    """
    log_error_with_context(
        logger,
        exc,
        context={
            "request_id": getattr(request.state, 'request_id', None),
            "method": request.method,
            "url": str(request.url),
            "error_type": type(exc).__name__
        }
    )
    
    return create_error_response(
        request=request,
        status_code=exc.status_code,
        message=exc.detail,
        error_code=exc.error_code
    )

async def http_exception_handler(
    request: Request, 
    exc: Union[HTTPException, StarletteHTTPException]
) -> JSONResponse:
    """
    HTTP 예외 핸들러
    """
    log_error_with_context(
        logger,
        exc,
        context={
            "request_id": getattr(request.state, 'request_id', None),
            "method": request.method,
            "url": str(request.url),
            "status_code": exc.status_code
        }
    )
    
    return create_error_response(
        request=request,
        status_code=exc.status_code,
        message=exc.detail,
        error_code="HTTP_ERROR"
    )

async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    요청 검증 예외 핸들러
    """
    # 검증 에러 메시지 포맷팅
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    error_message = "요청 데이터 검증에 실패했습니다"
    error_detail = "; ".join(errors)
    
    log_error_with_context(
        logger,
        exc,
        context={
            "request_id": getattr(request.state, 'request_id', None),
            "method": request.method,
            "url": str(request.url),
            "validation_errors": errors
        }
    )
    
    return create_error_response(
        request=request,
        status_code=422,
        message=error_message,
        detail=error_detail,
        error_code="VALIDATION_ERROR"
    )

async def database_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    데이터베이스 예외 핸들러
    """
    log_error_with_context(
        logger,
        exc,
        context={
            "request_id": getattr(request.state, 'request_id', None),
            "method": request.method,
            "url": str(request.url),
            "db_error": str(exc)
        }
    )
    
    # 프로덕션에서는 상세한 DB 에러를 숨김
    from app.core.config import settings
    
    if settings.DEBUG:
        error_detail = str(exc)
    else:
        error_detail = "데이터베이스 처리 중 오류가 발생했습니다"
    
    return create_error_response(
        request=request,
        status_code=500,
        message="데이터베이스 오류",
        detail=error_detail,
        error_code="DATABASE_ERROR"
    )

async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    일반 예외 핸들러 (마지막 fallback)
    """
    log_error_with_context(
        logger,
        exc,
        context={
            "request_id": getattr(request.state, 'request_id', None),
            "method": request.method,
            "url": str(request.url),
            "exception_type": type(exc).__name__
        }
    )
    
    # 프로덕션에서는 상세한 에러를 숨김
    from app.core.config import settings
    
    if settings.DEBUG:
        error_detail = str(exc)
    else:
        error_detail = "서버 내부 오류가 발생했습니다"
    
    return create_error_response(
        request=request,
        status_code=500,
        message="내부 서버 오류",
        detail=error_detail,
        error_code="INTERNAL_ERROR"
    )

def setup_exception_handlers(app):
    """
    모든 예외 핸들러 등록
    """
    # 커스텀 예외 핸들러들
    app.add_exception_handler(UserNotFoundError, custom_exception_handler)
    app.add_exception_handler(UserAlreadyExistsError, custom_exception_handler)
    app.add_exception_handler(InvalidCredentialsError, custom_exception_handler)
    app.add_exception_handler(InsufficientPermissionError, custom_exception_handler)
    app.add_exception_handler(HostingNotFoundError, custom_exception_handler)
    app.add_exception_handler(HostingAlreadyExistsError, custom_exception_handler)
    app.add_exception_handler(VMOperationError, custom_exception_handler)
    app.add_exception_handler(WebHostingException, custom_exception_handler)
    
    # 표준 FastAPI 예외 핸들러들
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 데이터베이스 예외 핸들러
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    # 일반 예외 핸들러 (마지막 fallback)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("모든 예외 핸들러가 등록되었습니다.")

# 특정 예외별 커스텀 핸들러 (필요시 사용)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    """사용자 없음 예외 전용 핸들러"""
    return create_error_response(
        request=request,
        status_code=404,
        message="사용자를 찾을 수 없습니다",
        error_code="USER_NOT_FOUND"
    )

async def insufficient_permission_handler(request: Request, exc: InsufficientPermissionError):
    """권한 부족 예외 전용 핸들러"""
    return create_error_response(
        request=request,
        status_code=403,
        message="접근 권한이 없습니다",
        error_code="INSUFFICIENT_PERMISSION"
    )

async def vm_operation_error_handler(request: Request, exc: VMOperationError):
    """VM 운영 오류 전용 핸들러"""
    return create_error_response(
        request=request,
        status_code=500,
        message="VM 운영 중 오류가 발생했습니다",
        detail=exc.detail,
        error_code="VM_OPERATION_ERROR"
    ) 