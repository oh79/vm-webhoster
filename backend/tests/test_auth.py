"""
인증 API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestAuthRegister:
    """회원가입 테스트"""
    
    def test_register_success(self, client: TestClient, test_user_data):
        """성공적인 회원가입 테스트"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "회원가입이 완료되었습니다."
        assert "data" in data
        assert data["data"]["email"] == test_user_data["email"]
        assert data["data"]["username"] == test_user_data["username"]
        assert "id" in data["data"]
        assert "password" not in data["data"]  # 비밀번호는 응답에 포함되지 않아야 함
    
    def test_register_duplicate_email(self, client: TestClient, created_user, test_user_data):
        """중복 이메일로 회원가입 시도 테스트"""
        # 같은 이메일로 다시 가입 시도
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["success"] is False
        assert "이미 등록된 이메일" in data["message"]
    
    def test_register_invalid_email(self, client: TestClient):
        """잘못된 이메일 형식으로 회원가입 테스트"""
        invalid_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False
        assert "검증" in data["message"]
    
    def test_register_weak_password(self, client: TestClient):
        """약한 비밀번호로 회원가입 테스트"""
        weak_password_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123"  # 너무 짧은 비밀번호
        }
        
        response = client.post("/api/v1/auth/register", json=weak_password_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False
    
    def test_register_missing_fields(self, client: TestClient):
        """필수 필드 누락 테스트"""
        incomplete_data = {
            "email": "test@example.com"
            # username, password 누락
        }
        
        response = client.post("/api/v1/auth/register", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """로그인 테스트"""
    
    def test_login_success(self, client: TestClient, created_user, test_user_data):
        """성공적인 로그인 테스트"""
        login_data = {
            "username": test_user_data["email"],  # OAuth2PasswordRequestForm은 username 필드 사용
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert "user" in data["data"]
        assert data["data"]["user"]["email"] == test_user_data["email"]
    
    def test_login_oauth2_token_endpoint(self, client: TestClient, created_user, test_user_data):
        """OAuth2 호환 토큰 엔드포인트 테스트"""
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/token", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient, created_user):
        """잘못된 로그인 정보 테스트"""
        login_data = {
            "username": "wrong@email.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
        assert "이메일 또는 비밀번호" in data["message"]
    
    def test_login_inactive_user(self, client: TestClient, inactive_user):
        """비활성화된 사용자 로그인 테스트"""
        login_data = {
            "username": "inactive@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
    
    def test_login_missing_credentials(self, client: TestClient):
        """로그인 정보 누락 테스트"""
        response = client.post("/api/v1/auth/login", data={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthMe:
    """현재 사용자 정보 조회 테스트"""
    
    def test_get_current_user_success(self, client: TestClient, auth_headers, created_user):
        """인증된 사용자 정보 조회 성공 테스트"""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == created_user.email
        assert data["data"]["username"] == created_user.username
        assert data["data"]["id"] == created_user.id
        assert data["data"]["is_active"] is True
    
    def test_get_current_user_no_token(self, client: TestClient):
        """토큰 없이 사용자 정보 조회 테스트"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
        assert "인증이 필요" in data["message"]
    
    def test_get_current_user_invalid_token(self, client: TestClient, invalid_token):
        """잘못된 토큰으로 사용자 정보 조회 테스트"""
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
    
    def test_get_current_user_expired_token(self, client: TestClient, expired_token):
        """만료된 토큰으로 사용자 정보 조회 테스트"""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False


class TestAuthRefresh:
    """토큰 갱신 테스트"""
    
    def test_refresh_token_success(self, client: TestClient, auth_headers):
        """토큰 갱신 성공 테스트"""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    def test_refresh_token_no_auth(self, client: TestClient):
        """인증 없이 토큰 갱신 시도 테스트"""
        response = client.post("/api/v1/auth/refresh")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
    
    def test_refresh_invalid_token(self, client: TestClient, invalid_token):
        """잘못된 토큰으로 갱신 시도 테스트"""
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.post("/api/v1/auth/refresh", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False


class TestAuthIntegration:
    """통합 인증 플로우 테스트"""
    
    def test_full_auth_flow(self, client: TestClient, test_user_data):
        """전체 인증 플로우 테스트: 회원가입 -> 로그인 -> 정보조회"""
        
        # 1. 회원가입
        register_response = client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # 2. 로그인
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        # 토큰 추출
        token_data = login_response.json()
        access_token = token_data["data"]["access_token"]
        
        # 3. 인증된 요청으로 사용자 정보 조회
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        
        user_data = me_response.json()
        assert user_data["data"]["email"] == test_user_data["email"]
        assert user_data["data"]["username"] == test_user_data["username"] 