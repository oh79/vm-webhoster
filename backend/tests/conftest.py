"""
pytest 테스트 설정 및 공통 fixture
"""
import asyncio
import pytest
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base  # 모든 모델이 포함된 Base import
from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_token_payload
from app.models.user import User
from app.models.hosting import Hosting, HostingStatus

# 테스트용 인메모리 SQLite 데이터베이스
TEST_DATABASE_URL = "sqlite:///:memory:"

# 테스트 데이터베이스 엔진 생성
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

# 테스트용 세션 팩토리
TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=test_engine
)

def override_get_db():
    """테스트용 데이터베이스 세션 의존성"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# 의존성 오버라이드
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """비동기 테스트를 위한 이벤트 루프"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """각 테스트마다 새로운 데이터베이스 세션 제공"""
    # 모든 모델이 메타데이터에 등록되었는지 확인
    from app.models.user import User
    from app.models.hosting import Hosting
    
    # 테이블 삭제 (이전 테스트 정리)
    Base.metadata.drop_all(bind=test_engine)
    
    # 테이블 생성
    Base.metadata.create_all(bind=test_engine)
    
    # 세션 생성
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # 테이블 삭제 (다음 테스트를 위해)
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """
    FastAPI 테스트 클라이언트
    db_session fixture에 의존하여 동일한 테스트 데이터베이스를 사용하도록 함
    """
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """테스트용 사용자 데이터"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }

@pytest.fixture
def test_user_data_2() -> Dict[str, Any]:
    """두 번째 테스트용 사용자 데이터"""
    return {
        "email": "test2@example.com",
        "username": "testuser2",
        "password": "testpassword456"
    }

@pytest.fixture
def created_user(db_session, test_user_data):
    """데이터베이스에 생성된 테스트 사용자"""
    from app.core.security import get_password_hash
    
    user = User(
        email=test_user_data["email"],
        username=test_user_data["username"],
        hashed_password=get_password_hash(test_user_data["password"]),
        is_active=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

@pytest.fixture
def created_user_2(db_session, test_user_data_2):
    """데이터베이스에 생성된 두 번째 테스트 사용자"""
    from app.core.security import get_password_hash
    
    user = User(
        email=test_user_data_2["email"],
        username=test_user_data_2["username"],
        hashed_password=get_password_hash(test_user_data_2["password"]),
        is_active=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

@pytest.fixture
def auth_token(created_user) -> str:
    """인증된 사용자의 JWT 토큰"""
    from datetime import datetime, timedelta
    from jose import jwt
    
    # 직접 페이로드 생성 (테스트용으로 1일 만료)
    payload = {
        "sub": str(created_user.id),
        "email": created_user.email,
        "exp": datetime.utcnow() + timedelta(days=1),  # 1일 만료
        "type": "access_token"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@pytest.fixture
def auth_token_2(created_user_2) -> str:
    """두 번째 사용자의 JWT 토큰"""
    from datetime import datetime, timedelta
    from jose import jwt
    
    # 직접 페이로드 생성 (테스트용으로 1일 만료)
    payload = {
        "sub": str(created_user_2.id),
        "email": created_user_2.email,
        "exp": datetime.utcnow() + timedelta(days=1),  # 1일 만료
        "type": "access_token"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@pytest.fixture
def auth_headers(auth_token) -> Dict[str, str]:
    """인증 헤더"""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def auth_headers_2(auth_token_2) -> Dict[str, str]:
    """두 번째 사용자의 인증 헤더"""
    return {"Authorization": f"Bearer {auth_token_2}"}

@pytest.fixture
def test_hosting_data() -> Dict[str, Any]:
    """테스트용 호스팅 데이터"""
    return {
        "vm_id": "test-vm-001",
        "vm_ip": "192.168.1.100",
        "ssh_port": 10022,
        "status": HostingStatus.RUNNING
    }

@pytest.fixture
def created_hosting(db_session, created_user, test_hosting_data):
    """데이터베이스에 생성된 테스트 호스팅"""
    hosting = Hosting(
        user_id=created_user.id,
        vm_id=test_hosting_data["vm_id"],
        vm_ip=test_hosting_data["vm_ip"],
        ssh_port=test_hosting_data["ssh_port"],
        status=HostingStatus.RUNNING
    )
    
    db_session.add(hosting)
    db_session.commit()
    db_session.refresh(hosting)
    
    return hosting

# 비활성화된 사용자 fixture
@pytest.fixture
def inactive_user(db_session):
    """비활성화된 테스트 사용자"""
    from app.core.security import get_password_hash
    
    user = User(
        email="inactive@example.com",
        username="inactiveuser",
        hashed_password=get_password_hash("password123"),
        is_active=False
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

# 잘못된 토큰 fixture
@pytest.fixture
def invalid_token() -> str:
    """잘못된 JWT 토큰"""
    return "invalid.jwt.token"

@pytest.fixture
def expired_token() -> str:
    """만료된 JWT 토큰 (테스트용)"""
    from datetime import datetime, timedelta
    from jose import jwt
    
    # 과거 시간으로 만료된 토큰 생성
    payload = {
        "sub": "999",
        "email": "expired@example.com",
        "exp": datetime.utcnow() - timedelta(hours=1),  # 1시간 전 만료
        "type": "access_token"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM) 