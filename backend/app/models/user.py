"""
사용자 모델 정의
"""
from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    """사용자 모델"""
    __tablename__ = "users"
    
    # 사용자 기본 정보
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 관계 설정 - 사용자와 호스팅 (1:1 관계)
    hosting = relationship("Hosting", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>" 