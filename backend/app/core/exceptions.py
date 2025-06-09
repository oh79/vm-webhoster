"""
커스텀 예외 클래스 및 예외 처리기
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

class WebHostingException(HTTPException):
    """웹 호스팅 서비스 기본 예외"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code

class UserNotFoundError(WebHostingException):
    """사용자를 찾을 수 없음"""
    def __init__(self, detail: str = "사용자를 찾을 수 없습니다."):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="USER_NOT_FOUND"
        )

class UserAlreadyExistsError(WebHostingException):
    """사용자가 이미 존재함"""
    def __init__(self, detail: str = "이미 등록된 이메일입니다."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="USER_ALREADY_EXISTS"
        )

class InvalidCredentialsError(WebHostingException):
    """인증 정보 오류"""
    def __init__(self, detail: str = "이메일 또는 비밀번호가 올바르지 않습니다."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="INVALID_CREDENTIALS"
        )

class HostingNotFoundError(WebHostingException):
    """호스팅을 찾을 수 없음"""
    def __init__(self, detail: str = "호스팅을 찾을 수 없습니다."):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="HOSTING_NOT_FOUND"
        )

class HostingAlreadyExistsError(WebHostingException):
    """호스팅이 이미 존재함"""
    def __init__(self, detail: str = "이미 호스팅을 보유하고 있습니다."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="HOSTING_ALREADY_EXISTS"
        )

class VMOperationError(WebHostingException):
    """VM 운영 오류"""
    def __init__(self, detail: str = "VM 운영 중 오류가 발생했습니다."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="VM_OPERATION_ERROR"
        )

class InsufficientPermissionError(WebHostingException):
    """권한 부족"""
    def __init__(self, detail: str = "해당 작업을 수행할 권한이 없습니다."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="INSUFFICIENT_PERMISSION"
        )

# 예외 처리기들
async def webhostingexception_handler(request: Request, exc: WebHostingException):
    """웹 호스팅 서비스 예외 처리기"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": exc.error_code,
            "details": None
        }
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    """Pydantic 검증 오류 처리기"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "입력 데이터 검증에 실패했습니다.",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """데이터베이스 무결성 오류 처리기"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "message": "데이터 무결성 오류가 발생했습니다.",
            "error_code": "INTEGRITY_ERROR",
            "details": None
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리기"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "서버 내부 오류가 발생했습니다.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": None
        }
    ) 