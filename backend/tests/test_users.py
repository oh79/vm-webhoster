"""
사용자 API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestUserProfile:
    """사용자 프로필 테스트"""
    
    def test_get_my_profile_success(self, client: TestClient, auth_headers, created_user):
        """내 프로필 조회 성공 테스트"""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == created_user.id
        assert data["data"]["email"] == created_user.email
        assert data["data"]["username"] == created_user.username
        assert data["data"]["is_active"] is True
        assert "created_at" in data["data"]
        assert "hashed_password" not in data["data"]  # 비밀번호는 응답에 포함되지 않아야 함
    
    def test_update_my_profile_success(self, client: TestClient, auth_headers, created_user):
        """내 프로필 수정 성공 테스트"""
        update_data = {
            "username": "updated_username",
            "email": created_user.email  # 이메일은 동일하게 유지
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "updated_username"
        assert data["data"]["email"] == created_user.email
    
    def test_update_profile_duplicate_email(self, client: TestClient, auth_headers, created_user_2):
        """중복 이메일로 프로필 수정 시도 테스트"""
        update_data = {
            "email": created_user_2.email,  # 다른 사용자의 이메일
            "username": "newusername"
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["success"] is False
        assert "이미 사용 중인 이메일" in data["message"]
    
    def test_update_profile_invalid_email(self, client: TestClient, auth_headers):
        """잘못된 이메일 형식으로 프로필 수정 테스트"""
        update_data = {
            "email": "invalid-email-format",
            "username": "validusername"
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False


class TestPasswordChange:
    """비밀번호 변경 테스트"""
    
    def test_change_password_success(self, client: TestClient, auth_headers, test_user_data):
        """비밀번호 변경 성공 테스트"""
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "new_secure_password123"
        }
        
        response = client.post("/api/v1/users/me/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "비밀번호가 성공적으로 변경되었습니다."
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """잘못된 현재 비밀번호로 변경 시도 테스트"""
        password_data = {
            "current_password": "wrong_password",
            "new_password": "new_secure_password123"
        }
        
        response = client.post("/api/v1/users/me/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "현재 비밀번호가 올바르지 않습니다" in data["message"]
    
    def test_change_password_weak_new_password(self, client: TestClient, auth_headers, test_user_data):
        """약한 새 비밀번호로 변경 시도 테스트"""
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "123"  # 너무 짧은 비밀번호
        }
        
        response = client.post("/api/v1/users/me/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False
    
    def test_change_password_same_as_current(self, client: TestClient, auth_headers, test_user_data):
        """현재 비밀번호와 동일한 새 비밀번호로 변경 시도 테스트"""
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": test_user_data["password"]  # 동일한 비밀번호
        }
        
        response = client.post("/api/v1/users/me/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "새 비밀번호는 현재 비밀번호와 달라야 합니다" in data["message"]


class TestAccountDeactivation:
    """계정 비활성화 테스트"""
    
    def test_deactivate_account_success(self, client: TestClient, auth_headers, test_user_data):
        """계정 비활성화 성공 테스트"""
        deactivate_data = {
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/users/me/deactivate", json=deactivate_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "계정이 비활성화되었습니다."
    
    def test_deactivate_account_wrong_password(self, client: TestClient, auth_headers):
        """잘못된 비밀번호로 계정 비활성화 시도 테스트"""
        deactivate_data = {
            "password": "wrong_password"
        }
        
        response = client.post("/api/v1/users/me/deactivate", json=deactivate_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "비밀번호가 올바르지 않습니다" in data["message"]


class TestUserLookup:
    """사용자 조회 테스트"""
    
    def test_get_user_by_id_success(self, client: TestClient, auth_headers, created_user_2):
        """사용자 ID로 조회 성공 테스트"""
        response = client.get(f"/api/v1/users/{created_user_2.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == created_user_2.id
        assert data["data"]["username"] == created_user_2.username
        assert data["data"]["email"] == created_user_2.email
        assert "hashed_password" not in data["data"]
    
    def test_get_user_by_id_not_found(self, client: TestClient, auth_headers):
        """존재하지 않는 사용자 ID로 조회 테스트"""
        non_existent_id = 99999
        response = client.get(f"/api/v1/users/{non_existent_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert "사용자를 찾을 수 없습니다" in data["message"]
    
    def test_get_users_list(self, client: TestClient, auth_headers, created_user, created_user_2):
        """사용자 목록 조회 테스트"""
        response = client.get("/api/v1/users", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "users" in data["data"]
        assert "pagination" in data["data"]
        
        users = data["data"]["users"]
        assert len(users) >= 2  # 최소 2명의 사용자가 있어야 함
        
        # 페이지네이션 정보 확인
        pagination = data["data"]["pagination"]
        assert "page" in pagination
        assert "size" in pagination
        assert "total" in pagination
    
    def test_get_users_list_with_pagination(self, client: TestClient, auth_headers):
        """페이지네이션을 사용한 사용자 목록 조회 테스트"""
        response = client.get("/api/v1/users?page=1&size=5", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        
        pagination = data["data"]["pagination"]
        assert pagination["page"] == 1
        assert pagination["size"] == 5


class TestUserAuthentication:
    """사용자 인증 관련 테스트"""
    
    def test_access_with_no_token(self, client: TestClient):
        """토큰 없이 보호된 엔드포인트 접근 테스트"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
        assert "인증이 필요" in data["message"]
    
    def test_access_with_invalid_token(self, client: TestClient, invalid_token):
        """잘못된 토큰으로 보호된 엔드포인트 접근 테스트"""
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
    
    def test_access_with_expired_token(self, client: TestClient, expired_token):
        """만료된 토큰으로 보호된 엔드포인트 접근 테스트"""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False


class TestUserIntegration:
    """사용자 통합 테스트"""
    
    def test_user_profile_update_flow(self, client: TestClient, auth_headers, test_user_data):
        """사용자 프로필 업데이트 전체 플로우 테스트"""
        
        # 1. 현재 프로필 조회
        profile_response = client.get("/api/v1/users/me", headers=auth_headers)
        assert profile_response.status_code == status.HTTP_200_OK
        original_profile = profile_response.json()["data"]
        
        # 2. 프로필 업데이트
        update_data = {
            "username": "updated_user",
            "email": original_profile["email"]  # 이메일은 동일하게 유지
        }
        update_response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
        assert update_response.status_code == status.HTTP_200_OK
        
        # 3. 업데이트된 프로필 확인
        updated_profile_response = client.get("/api/v1/users/me", headers=auth_headers)
        assert updated_profile_response.status_code == status.HTTP_200_OK
        updated_profile = updated_profile_response.json()["data"]
        
        assert updated_profile["username"] == "updated_user"
        assert updated_profile["email"] == original_profile["email"]
        assert updated_profile["id"] == original_profile["id"]
    
    def test_password_change_and_login_flow(self, client: TestClient, auth_headers, test_user_data):
        """비밀번호 변경 후 로그인 플로우 테스트"""
        
        # 1. 비밀번호 변경
        new_password = "new_secure_password456"
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": new_password
        }
        change_response = client.post("/api/v1/users/me/change-password", json=password_data, headers=auth_headers)
        assert change_response.status_code == status.HTTP_200_OK
        
        # 2. 새 비밀번호로 로그인 시도
        login_data = {
            "username": test_user_data["email"],
            "password": new_password
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        # 3. 이전 비밀번호로 로그인 시도 (실패해야 함)
        old_login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        old_login_response = client.post("/api/v1/auth/login", data=old_login_data)
        assert old_login_response.status_code == status.HTTP_401_UNAUTHORIZED 