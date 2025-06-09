"""
보안 관련 유틸리티 함수들
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from .config import settings

# 비밀번호 해싱 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 해시된 비밀번호를 비교"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호를 해시화"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Union[dict, None]:
    """JWT 토큰 검증 및 페이로드 반환"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def verify_access_token(token: str) -> Dict[str, Any]:
    """
    JWT 액세스 토큰 검증 및 페이로드 반환
    예외를 발생시키는 버전 (dependencies.py에서 사용)
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 토큰 타입 확인
        if payload.get("type") != "access_token":
            raise JWTError("Invalid token type")
        
        # 만료 시간 확인 (자동으로 확인되지만 명시적으로 처리)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise JWTError("Token expired")
        
        return payload
        
    except JWTError as e:
        raise SecurityError(f"토큰 검증 실패: {str(e)}")

def create_token_payload(user_id: int, email: str) -> dict:
    """토큰 페이로드 생성"""
    return {
        "sub": str(user_id),  # subject (사용자 ID)
        "email": email,
        "iat": datetime.utcnow(),  # issued at
        "type": "access_token"
    }

def extract_user_id_from_token(token: str) -> Optional[int]:
    """토큰에서 사용자 ID 추출"""
    payload = verify_token(token)
    if payload and "sub" in payload:
        try:
            return int(payload["sub"])
        except (ValueError, TypeError):
            return None
    return None

def validate_password_strength(password: str) -> bool:
    """비밀번호 강도 검증"""
    if len(password) < 8:
        return False
    
    # 최소 하나의 숫자, 하나의 문자 포함 확인
    has_digit = any(c.isdigit() for c in password)
    has_alpha = any(c.isalpha() for c in password)
    
    return has_digit and has_alpha

class SecurityError(HTTPException):
    """보안 관련 예외"""
    def __init__(self, detail: str = "Security error"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) 