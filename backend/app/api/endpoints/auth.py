"""
인증 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest
from app.schemas.common import StandardResponse
from app.services.user_service import UserService
from app.core.dependencies import get_current_user
from app.utils.response_utils import create_success_response
from app.utils.logging_utils import log_request_info, get_logger
from app.core.exceptions import (
    UserAlreadyExistsError, 
    InvalidCredentialsError,
    UserNotFoundError
)

# 라우터 설정
router = APIRouter(tags=["인증"])
logger = get_logger("api.auth")

@router.post(
    "/register",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    description="새 사용자 계정을 생성합니다."
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    새 사용자 회원가입
    
    - **email**: 이메일 주소 (고유)
    - **username**: 사용자명 (고유, 2-50자)
    - **password**: 비밀번호 (8자 이상, 숫자+문자 포함)
    """
    log_request_info("POST", "/auth/register", extra_info={"email": user_data.email})
    
    try:
        user_service = UserService(db)
        user = user_service.create_user(user_data)
        
        logger.info(f"새 사용자 생성: {user.email} (ID: {user.id})")
        
        return create_success_response(
            message="회원가입이 완료되었습니다.",
            data=UserResponse.model_validate(user)
        )
        
    except UserAlreadyExistsError as e:
        logger.warning(f"회원가입 실패 - 중복: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"회원가입 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다."
        )

@router.post(
    "/login",
    response_model=StandardResponse[dict],
    summary="로그인",
    description="이메일과 비밀번호로 로그인하여 액세스 토큰을 발급받습니다."
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    사용자 로그인 (OAuth2 호환)
    
    - **username**: 등록된 이메일 주소 (OAuth2 표준에서는 username 필드 사용)
    - **password**: 비밀번호
    
    성공 시 JWT 액세스 토큰과 사용자 정보를 반환합니다.
    """
    log_request_info("POST", "/auth/login", extra_info={"email": form_data.username})
    
    try:
        user_service = UserService(db)
        
        # 사용자 인증 (OAuth2에서는 username 필드에 이메일을 사용)
        user = user_service.authenticate_user(form_data.username, form_data.password)
        
        if not user:
            logger.warning(f"로그인 실패: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 토큰 생성
        token = user_service.create_access_token_for_user(user)
        
        logger.info(f"로그인 성공: {user.email} (ID: {user.id})")
        
        return create_success_response(
            message="로그인이 완료되었습니다.",
            data={
                "access_token": token.access_token,
                "token_type": token.token_type,
                "expires_in": token.expires_in,
                "user": UserResponse.model_validate(user).model_dump()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )

@router.post(
    "/token",
    response_model=Token,
    summary="토큰 발급 (OAuth2 호환)",
    description="OAuth2 표준 형식으로 토큰을 발급합니다."
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 호환 토큰 발급
    
    FastAPI 자동 문서화에서 사용할 수 있는 표준 OAuth2 로그인입니다.
    """
    log_request_info("POST", "/auth/token", extra_info={"username": form_data.username})
    
    try:
        user_service = UserService(db)
        
        # OAuth2에서는 username 필드에 이메일을 사용
        user = user_service.authenticate_user(form_data.username, form_data.password)
        
        if not user:
            logger.warning(f"OAuth2 로그인 실패: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = user_service.create_access_token_for_user(user)
        
        logger.info(f"OAuth2 로그인 성공: {user.email} (ID: {user.id})")
        
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 로그인 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )

@router.post(
    "/refresh",
    response_model=StandardResponse[Token],
    summary="토큰 갱신",
    description="기존 토큰을 사용하여 새로운 토큰을 발급받습니다."
)
def refresh_token(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    토큰 갱신
    
    현재 유효한 토큰을 사용하여 새로운 토큰을 발급받습니다.
    """
    log_request_info("POST", "/auth/refresh", user_id=current_user.id)
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(current_user.id)
        
        if not user or not user.is_active:
            raise UserNotFoundError("사용자를 찾을 수 없거나 비활성화되었습니다.")
        
        # 새 토큰 생성
        token = user_service.create_access_token_for_user(user)
        
        logger.info(f"토큰 갱신: {user.email} (ID: {user.id})")
        
        return create_success_response(
            message="토큰이 갱신되었습니다.",
            data=token
        )
        
    except UserNotFoundError as e:
        logger.warning(f"토큰 갱신 실패: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"토큰 갱신 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다."
        )

@router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    summary="현재 사용자 정보 조회",
    description="JWT 토큰으로 인증된 현재 사용자의 정보를 반환합니다."
)
def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자 정보 조회
    
    Authorization 헤더에 Bearer 토큰을 포함해야 합니다.
    """
    log_request_info("GET", "/auth/me", user_id=current_user.id)
    
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(current_user.id)
        
        if not user or not user.is_active:
            raise UserNotFoundError("사용자를 찾을 수 없거나 비활성화되었습니다.")
        
        logger.info(f"사용자 정보 조회: {user.email} (ID: {user.id})")
        
        return create_success_response(
            message="사용자 정보를 성공적으로 조회했습니다.",
            data=UserResponse.model_validate(user)
        )
        
    except UserNotFoundError as e:
        logger.warning(f"사용자 정보 조회 실패: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"사용자 정보 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 조회 중 오류가 발생했습니다."
        ) 