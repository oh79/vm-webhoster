"""
사용자 서비스 - 사용자 관련 비즈니스 로직
"""
from typing import Optional, List
from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, Token
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    create_token_payload
)
from app.core.config import settings
from app.core.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InsufficientPermissionError
)

class UserService:
    """사용자 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        새 사용자 생성
        """
        # 이메일 중복 확인
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise UserAlreadyExistsError("이미 등록된 이메일입니다.")
        
        # 사용자명 중복 확인
        existing_username = self.db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise UserAlreadyExistsError("이미 사용 중인 사용자명입니다.")
        
        try:
            # 비밀번호 해싱
            hashed_password = get_password_hash(user_data.password)
            
            # 사용자 생성
            db_user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
                is_active=True
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            return db_user
            
        except IntegrityError:
            self.db.rollback()
            raise UserAlreadyExistsError("사용자 정보가 이미 존재합니다.")
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        사용자 인증 (로그인)
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
            
        if not user.is_active:
            return None
            
        return user
    
    def create_access_token_for_user(self, user: User) -> Token:
        """
        사용자용 액세스 토큰 생성
        """
        # 토큰 페이로드 생성
        token_data = create_token_payload(user.id, user.email)
        
        # 토큰 만료 시간 설정
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # 토큰 생성
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 초 단위
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        ID로 사용자 조회
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        이메일로 사용자 조회
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        사용자 목록 조회 (페이지네이션)
        """
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update_user(self, user_id: int, user_data: UserUpdate, current_user_id: int) -> User:
        """
        사용자 정보 업데이트
        """
        # 권한 확인 (본인만 수정 가능)
        if user_id != current_user_id:
            raise InsufficientPermissionError("본인의 정보만 수정할 수 있습니다.")
        
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # 수정할 필드만 업데이트
        update_data = user_data.model_dump(exclude_unset=True)
        
        # 사용자명 중복 확인
        if "username" in update_data:
            existing_user = self.db.query(User).filter(
                User.username == update_data["username"],
                User.id != user_id
            ).first()
            if existing_user:
                raise UserAlreadyExistsError("이미 사용 중인 사용자명입니다.")
        
        try:
            for field, value in update_data.items():
                setattr(user, field, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            return user
            
        except IntegrityError:
            self.db.rollback()
            raise UserAlreadyExistsError("사용자 정보 업데이트에 실패했습니다.")
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        비밀번호 변경
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # 현재 비밀번호 확인
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError("현재 비밀번호가 올바르지 않습니다.")
        
        # 새 비밀번호가 현재 비밀번호와 같은지 확인
        if verify_password(new_password, user.hashed_password):
            raise InvalidCredentialsError("새 비밀번호는 현재 비밀번호와 달라야 합니다.")
        
        # 새 비밀번호 해싱 및 저장
        user.hashed_password = get_password_hash(new_password)
        
        self.db.commit()
        return True
    
    def deactivate_user(self, user_id: int, password: str) -> User:
        """
        사용자 비활성화
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # 비밀번호 확인
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("비밀번호가 올바르지 않습니다.")
        
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_count(self) -> int:
        """
        전체 사용자 수 조회
        """
        return self.db.query(User).count()
    
    def get_active_user_count(self) -> int:
        """
        활성 사용자 수 조회
        """
        return self.db.query(User).filter(User.is_active == True).count() 