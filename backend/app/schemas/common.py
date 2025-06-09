"""
공통 Pydantic 스키마 정의
"""
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

# Generic 타입 변수
DataType = TypeVar("DataType")

class StandardResponse(BaseModel, Generic[DataType]):
    """표준 API 응답 모델"""
    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[DataType] = Field(None, description="응답 데이터")

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    success: bool = Field(False, description="요청 성공 여부")
    message: str = Field(..., description="에러 메시지")
    error_code: Optional[str] = Field(None, description="에러 코드")
    details: Optional[dict] = Field(None, description="에러 상세 정보")

class PaginationParams(BaseModel):
    """페이지네이션 파라미터"""
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(10, ge=1, le=100, description="페이지 크기")

class PaginatedResponse(BaseModel, Generic[DataType]):
    """페이지네이션된 응답 모델"""
    items: list[DataType] = Field(..., description="데이터 목록")
    total: int = Field(..., description="전체 항목 수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")

class HealthCheck(BaseModel):
    """헬스체크 응답 모델"""
    status: str = Field(..., description="서비스 상태")
    service: str = Field(..., description="서비스 이름")
    version: str = Field(..., description="서비스 버전")
    timestamp: str = Field(..., description="응답 시간") 