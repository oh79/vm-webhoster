"""
사용자 관련 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserResponse, UserUpdate, PasswordChange, AccountDeactivate
from app.schemas.common import StandardResponse, PaginatedResponse, PaginationParams
from app.services.user_service import UserService
from app.core.dependencies import get_current_user, get_current_user_id
from app.utils.response_utils import (
    create_success_response, 
    create_paginated_response,
    validate_pagination_params,
    calculate_offset
)
from app.utils.logging_utils import log_request_info, get_logger
from app.core.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InsufficientPermissionError
)

# 라우터 설정
router = APIRouter(tags=["사용자"])
logger = get_logger("api.users")

@router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    summary="내 프로필 조회",
    description="현재 로그인한 사용자의 프로필 정보를 조회합니다."
)
def get_my_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    현재 사용자 프로필 조회
    
    JWT 토큰을 통해 인증된 사용자의 프로필 정보를 반환합니다.
    """
    log_request_info("GET", "/users/me", user_id=current_user.id)
    
    logger.info(f"프로필 조회: {current_user.email} (ID: {current_user.id})")
    
    return create_success_response(
        message="프로필 정보를 조회했습니다.",
        data=current_user
    )

@router.put(
    "/me",
    response_model=StandardResponse[UserResponse],
    summary="내 프로필 수정",
    description="현재 로그인한 사용자의 프로필 정보를 수정합니다."
)
def update_my_profile(
    user_data: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    현재 사용자 프로필 수정
    
    - **username**: 사용자명 (선택사항)
    - **is_active**: 활성 상태 (선택사항, 본인만 비활성화 가능)
    """
    log_request_info("PUT", "/users/me", user_id=current_user_id)
    
    try:
        user_service = UserService(db)
        user = user_service.update_user(current_user_id, user_data, current_user_id)
        
        logger.info(f"프로필 수정: {user.email} (ID: {user.id})")
        
        return create_success_response(
            message="프로필이 수정되었습니다.",
            data=UserResponse.model_validate(user)
        )
        
    except UserNotFoundError as e:
        logger.warning(f"프로필 수정 실패 - 사용자 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except UserAlreadyExistsError as e:
        logger.warning(f"프로필 수정 실패 - 중복: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"프로필 수정 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 수정 중 오류가 발생했습니다."
        )

@router.post(
    "/me/change-password",
    response_model=StandardResponse[dict],
    summary="비밀번호 변경",
    description="현재 사용자의 비밀번호를 변경합니다."
)
def change_password(
    password_data: PasswordChange,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    비밀번호 변경
    
    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호 (8자 이상, 숫자+문자 포함)
    """
    log_request_info("POST", "/users/me/change-password", user_id=current_user_id)
    
    try:
        user_service = UserService(db)
        success = user_service.change_password(
            current_user_id, 
            password_data.current_password, 
            password_data.new_password
        )
        
        if success:
            logger.info(f"비밀번호 변경 성공: 사용자 ID {current_user_id}")
            
            return create_success_response(
                message="비밀번호가 성공적으로 변경되었습니다.",
                data={"changed": True}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="비밀번호 변경에 실패했습니다."
            )
            
    except InvalidCredentialsError as e:
        logger.warning(f"비밀번호 변경 실패 - 인증 오류: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail
        )
    except UserNotFoundError as e:
        logger.warning(f"비밀번호 변경 실패 - 사용자 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"비밀번호 변경 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 변경 중 오류가 발생했습니다."
        )

@router.post(
    "/me/deactivate",
    response_model=StandardResponse[UserResponse],
    summary="계정 비활성화",
    description="현재 사용자의 계정을 비활성화합니다."
)
def deactivate_account(
    deactivate_data: AccountDeactivate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    계정 비활성화
    
    - **password**: 계정 확인용 비밀번호
    
    계정을 비활성화하면 로그인할 수 없게 됩니다.
    """
    log_request_info("POST", "/users/me/deactivate", user_id=current_user_id)
    
    try:
        user_service = UserService(db)
        user = user_service.deactivate_user(current_user_id, deactivate_data.password)
        
        logger.info(f"계정 비활성화: {user.email} (ID: {user.id})")
        
        return create_success_response(
            message="계정이 비활성화되었습니다.",
            data=UserResponse.model_validate(user)
        )
        
    except UserNotFoundError as e:
        logger.warning(f"계정 비활성화 실패 - 사용자 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except InvalidCredentialsError as e:
        logger.warning(f"계정 비활성화 실패 - 비밀번호 오류: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail
        )
    except InsufficientPermissionError as e:
        logger.warning(f"계정 비활성화 실패 - 권한 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"계정 비활성화 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="계정 비활성화 중 오류가 발생했습니다."
        )

@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserResponse],
    summary="사용자 프로필 조회",
    description="특정 사용자의 공개 프로필 정보를 조회합니다."
)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_current_user_id)
):
    """
    특정 사용자 프로필 조회
    
    - **user_id**: 조회할 사용자 ID
    
    본인의 프로필이거나 공개 프로필만 조회할 수 있습니다.
    """
    log_request_info("GET", f"/users/{user_id}", user_id=current_user_id)
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise UserNotFoundError()
        
        # 본인이거나 활성 사용자만 조회 가능
        if user_id != current_user_id and not user.is_active:
            raise UserNotFoundError("사용자를 찾을 수 없습니다.")
        
        logger.info(f"사용자 프로필 조회: {user.email} (ID: {user.id})")
        
        return create_success_response(
            message="사용자 프로필을 조회했습니다.",
            data=UserResponse.model_validate(user)
        )
        
    except UserNotFoundError as e:
        logger.warning(f"사용자 프로필 조회 실패: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"사용자 프로필 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 프로필 조회 중 오류가 발생했습니다."
        )

@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="사용자 목록 조회",
    description="사용자 목록을 페이지네이션으로 조회합니다. (관리자 기능)"
)
def get_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    사용자 목록 조회
    
    - **page**: 페이지 번호 (1부터 시작)
    - **size**: 페이지 크기 (1-100)
    
    현재는 모든 인증된 사용자가 조회 가능합니다.
    """
    log_request_info("GET", "/users", user_id=current_user_id, extra_info={"page": page, "size": size})
    
    try:
        # 페이지네이션 파라미터 검증
        pagination = validate_pagination_params(page, size)
        offset = calculate_offset(pagination.page, pagination.size)
        
        user_service = UserService(db)
        users = user_service.get_users(skip=offset, limit=pagination.size)
        total_users = user_service.get_user_count()
        
        # UserResponse로 변환
        user_responses = [UserResponse.model_validate(user) for user in users]
        
        logger.info(f"사용자 목록 조회: 페이지 {page}, 크기 {size}, 전체 {total_users}개")
        
        return create_paginated_response(
            items=user_responses,
            total=total_users,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다."
        ) 