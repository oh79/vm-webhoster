"""
의존성 주입 - 인증, 권한, 데이터베이스 등
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.db.session import get_db
from app.core.config import settings
from app.core.security import verify_access_token
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.core.exceptions import UserNotFoundError, InvalidCredentialsError
from app.utils.logging_utils import get_logger

# OAuth2 설정
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    auto_error=False  # 선택적 인증을 위해 False로 설정
)

logger = get_logger("dependencies")

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    선택적 사용자 인증 (토큰이 없어도 None 반환)
    """
    if not token:
        return None
    
    try:
        # JWT 토큰 검증
        payload = verify_access_token(token)
        user_id: int = payload.get("sub")
        
        if user_id is None:
            return None
        
        # 사용자 조회
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            return None
        
        return user
        
    except (JWTError, ValueError, AttributeError):
        return None

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    필수 사용자 인증 (토큰이 없으면 401 에러)
    """
    if not token:
        logger.warning("토큰이 제공되지 않았습니다")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # JWT 토큰 검증
        payload = verify_access_token(token)
        user_id: int = payload.get("sub")
        
        if user_id is None:
            logger.warning("토큰에서 사용자 ID를 찾을 수 없습니다")
            raise InvalidCredentialsError("유효하지 않은 인증 정보입니다")
        
        # 사용자 조회
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            logger.warning(f"사용자 ID {user_id}를 찾을 수 없습니다")
            raise UserNotFoundError("사용자를 찾을 수 없습니다")
        
        if not user.is_active:
            logger.warning(f"비활성화된 사용자 접근 시도: {user.email}")
            raise InvalidCredentialsError("비활성화된 계정입니다")
        
        return UserResponse.model_validate(user)
        
    except JWTError as e:
        logger.warning(f"JWT 토큰 검증 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (UserNotFoundError, InvalidCredentialsError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"사용자 인증 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 처리 중 오류가 발생했습니다"
        )

def get_current_user_id(
    current_user: UserResponse = Depends(get_current_user)
) -> int:
    """
    현재 사용자 ID 반환
    """
    return current_user.id

def get_current_user_id_optional(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Optional[int]:
    """
    현재 사용자 ID 반환 (선택적)
    """
    return current_user.id if current_user else None

def get_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    활성 사용자만 허용
    """
    if not current_user.is_active:
        logger.warning(f"비활성화된 사용자 접근 시도: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    
    return current_user

def verify_user_permissions(
    target_user_id: int,
    current_user: UserResponse = Depends(get_current_user)
) -> bool:
    """
    사용자 권한 확인 (본인만 접근 가능)
    """
    if current_user.id != target_user_id:
        logger.warning(f"권한 없는 접근 시도: 사용자 {current_user.id} -> {target_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다"
        )
    
    return True

# 관리자 권한 확인 (향후 확장용)
def get_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    관리자 권한 확인 (향후 Role 기반 권한 시스템 구현 시 사용)
    """
    # 현재는 모든 사용자를 일반 사용자로 처리
    # 향후 User 모델에 role 필드 추가 시 확장
    return current_user

# 데이터베이스 트랜잭션 관리
def get_db_transaction():
    """
    트랜잭션 관리가 필요한 경우 사용할 의존성
    """
    db = next(get_db())
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# 페이지네이션 파라미터 의존성
def get_pagination_params(
    page: int = 1,
    size: int = 10
) -> dict:
    """
    페이지네이션 파라미터 검증 및 반환
    """
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = min(max(size, 1), 100)
    
    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size,
        "limit": size
    }

# 요청 ID 생성 (로깅용)
def get_request_id() -> str:
    """
    요청 추적을 위한 고유 ID 생성
    """
    import uuid
    return str(uuid.uuid4())

# API 버전 확인
def verify_api_version(api_version: str = "v1") -> str:
    """
    API 버전 확인
    """
    supported_versions = ["v1"]
    
    if api_version not in supported_versions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원되지 않는 API 버전입니다. 지원 버전: {', '.join(supported_versions)}"
        )
    
    return api_version 