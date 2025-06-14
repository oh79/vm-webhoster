"""
데이터베이스 세션 설정
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 동기 데이터베이스 엔진 설정
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG  # 개발 환경에서 SQL 쿼리 로깅
)

# SQLite 사용 시 비동기 엔진 생성 안함
async_engine = None
AsyncSessionLocal = None

# PostgreSQL 사용 시에만 비동기 엔진 생성
if settings.DATABASE_URL.startswith("postgresql"):
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    
    # 비동기 데이터베이스 엔진 설정 (PostgreSQL asyncpg 드라이버 사용)
    async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(
        async_database_url,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )
    
    # 비동기 세션 팩토리
    AsyncSessionLocal = sessionmaker(
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        bind=async_engine
    )

# 동기 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 데이터베이스 의존성 함수 (동기)
def get_db():
    """동기 데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 비동기 데이터베이스 의존성 함수
async def get_async_db():
    """비동기 데이터베이스 세션 의존성"""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database session is not available for SQLite")
    
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close() 