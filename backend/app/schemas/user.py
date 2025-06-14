"""
사용자 관련 Pydantic 스키마
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.security import validate_password_strength

class UserBase(BaseModel):
    """사용자 기본 정보"""
    email: EmailStr = Field(..., description="이메일 주소")
    username: str = Field(..., min_length=2, max_length=50, description="사용자명")

class UserCreate(UserBase):
    """사용자 생성 요청"""
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError('비밀번호는 최소 8자 이상이며, 숫자와 문자를 모두 포함해야 합니다.')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('사용자명은 공백일 수 없습니다.')
        return v.strip()

class UserUpdate(BaseModel):
    """사용자 정보 수정 요청"""
    email: Optional[EmailStr] = Field(None, description="이메일 주소")
    username: Optional[str] = Field(None, min_length=2, max_length=50, description="사용자명")
    is_active: Optional[bool] = Field(None, description="활성 상태")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None and not v.strip():
            raise ValueError('사용자명은 공백일 수 없습니다.')
        return v.strip() if v else v

class UserResponse(BaseModel):
    """사용자 응답 모델"""
    id: int = Field(..., description="사용자 ID")
    email: EmailStr = Field(..., description="이메일 주소")
    username: str = Field(..., description="사용자명")
    is_active: bool = Field(..., description="활성 상태")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    
    model_config = {"from_attributes": True}

class UserInDB(UserResponse):
    """데이터베이스의 사용자 정보 (해시된 비밀번호 포함)"""
    hashed_password: str = Field(..., description="해시된 비밀번호")

# 인증 관련 스키마
class Token(BaseModel):
    """JWT 토큰 응답"""
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간 (초)")

class TokenData(BaseModel):
    """토큰 데이터"""
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")

class PasswordChange(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, max_length=100, description="새 비밀번호")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError('새 비밀번호는 최소 8자 이상이며, 숫자와 문자를 모두 포함해야 합니다.')
        return v

class AccountDeactivate(BaseModel):
    """계정 비활성화 요청"""
    password: str = Field(..., description="계정 확인용 비밀번호") 