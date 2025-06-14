"""
API 응답 처리 유틸리티
"""
from typing import Any, Optional, TypeVar, Generic, List
from math import ceil
from app.schemas.common import StandardResponse, PaginatedResponse, PaginationParams

T = TypeVar('T')

def create_success_response(
    message: str,
    data: Optional[Any] = None
) -> StandardResponse[Any]:
    """
    성공 응답 생성
    """
    return StandardResponse[Any](
        success=True,
        message=message,
        data=data
    )

def create_paginated_response(
    items: List[T],
    total: int,
    pagination: PaginationParams
) -> PaginatedResponse[T]:
    """
    페이지네이션된 응답 생성
    """
    pages = ceil(total / pagination.size) if total > 0 else 0
    
    return PaginatedResponse[T](
        items=items,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pages
    )

def calculate_offset(page: int, size: int) -> int:
    """
    페이지네이션 오프셋 계산
    """
    return (page - 1) * size

def validate_pagination_params(page: int, size: int) -> PaginationParams:
    """
    페이지네이션 파라미터 검증 및 정규화
    """
    # 최소값 보정
    page = max(1, page)
    size = max(1, min(100, size))  # 최대 100개로 제한
    
    return PaginationParams(page=page, size=size) 