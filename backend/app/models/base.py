"""
SQLAlchemy Base 클래스 정의
"""
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# SQLAlchemy Base 클래스 생성
Base = declarative_base()

class BaseModel(Base):
    """모든 모델의 기본 클래스"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) 