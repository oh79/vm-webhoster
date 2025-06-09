"""
데이터베이스 Base 클래스 및 모든 모델 Import
Alembic이 모든 모델을 인식할 수 있도록 하는 파일
"""
from app.models.base import Base

# 모든 모델을 import하여 Alembic이 인식할 수 있도록 함
from app.models.user import User
from app.models.hosting import Hosting

# Base 클래스 및 모든 모델 export
__all__ = ["Base"] 