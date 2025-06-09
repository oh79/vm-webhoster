"""
호스팅 API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session

from app.models.hosting import Hosting, HostingStatus


class TestHostingCreation:
    """호스팅 생성 테스트"""
    
    def test_create_hosting_success(self, client: TestClient, auth_headers):
        """호스팅 생성 성공 테스트"""
        response = client.post(
            "/api/v1/host",
            json={},  # 호스팅 생성은 빈 객체 전송
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        hosting_data = data["data"]
        assert "id" in hosting_data
        assert hosting_data["user_id"] is not None
        assert hosting_data["vm_id"] is not None
        assert hosting_data["status"] in ["creating", "running"]
    
    def test_create_hosting_unauthorized(self, client: TestClient):
        """인증되지 않은 사용자의 호스팅 생성 시도"""
        response = client.post("/api/v1/host", json={})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_duplicate_hosting(self, client: TestClient, auth_headers, created_hosting):
        """중복 호스팅 생성 시도 테스트"""
        response = client.post(
            "/api/v1/host",
            json={},  # 호스팅 생성은 빈 객체 전송
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["success"] is False
        assert "이미" in data["message"]


class TestHostingRetrieve:
    """호스팅 조회 테스트"""
    
    def test_get_hosting_success(self, client: TestClient, auth_headers, created_hosting):
        """호스팅 조회 성공 테스트"""
        response = client.get("/api/v1/host", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        hosting_data = data["data"]
        assert hosting_data["id"] == created_hosting.id
        assert hosting_data["user_id"] == created_hosting.user_id
        assert hosting_data["vm_id"] == created_hosting.vm_id
    
    def test_get_hosting_not_found(self, client: TestClient, auth_headers):
        """호스팅이 없는 경우 조회 테스트"""
        response = client.get("/api/v1/host", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert "호스팅을 찾을 수 없습니다" in data["message"]
    
    def test_get_hosting_unauthorized(self, client: TestClient):
        """인증되지 않은 호스팅 조회 시도"""
        response = client.get("/api/v1/host")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestHostingDeletion:
    """호스팅 삭제 테스트"""
    
    def test_delete_hosting_success(self, client: TestClient, auth_headers, created_hosting):
        """호스팅 삭제 성공 테스트"""
        response = client.delete("/api/v1/host", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted"] is True
        assert "삭제" in data["message"]
    
    def test_delete_hosting_not_found(self, client: TestClient, auth_headers):
        """존재하지 않는 호스팅 삭제 시도"""
        response = client.delete("/api/v1/host", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert "호스팅을 찾을 수 없습니다" in data["message"]
    
    def test_delete_hosting_unauthorized(self, client: TestClient):
        """인증되지 않은 호스팅 삭제 시도"""
        response = client.delete("/api/v1/host")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestHostingOperations:
    """호스팅 운영 테스트"""
    
    def test_start_hosting_success(self, client: TestClient, auth_headers, created_hosting):
        """호스팅 시작 성공 테스트"""
        operation_data = {"operation": "start"}
        response = client.post(
            f"/api/v1/hosting/{created_hosting.id}/operations",
            json=operation_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "start" in data["message"].lower()
    
    def test_stop_hosting_success(self, client: TestClient, auth_headers, created_hosting):
        """호스팅 중지 성공 테스트"""
        operation_data = {"operation": "stop"}
        response = client.post(
            f"/api/v1/hosting/{created_hosting.id}/operations",
            json=operation_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "stop" in data["message"].lower()
    
    def test_restart_hosting_success(self, client: TestClient, auth_headers, created_hosting):
        """호스팅 재시작 성공 테스트"""
        operation_data = {"operation": "restart"}
        response = client.post(
            f"/api/v1/hosting/{created_hosting.id}/operations",
            json=operation_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "restart" in data["message"].lower()
    
    def test_delete_hosting_success(self, client: TestClient, auth_headers, created_hosting):
        """호스팅 삭제 성공 테스트"""
        operation_data = {"operation": "delete"}
        response = client.post(
            f"/api/v1/hosting/{created_hosting.id}/operations",
            json=operation_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "delete" in data["message"].lower()
    
    def test_invalid_operation(self, client: TestClient, auth_headers, created_hosting):
        """잘못된 운영 명령 테스트"""
        operation_data = {"operation": "invalid_operation"}
        response = client.post(
            f"/api/v1/hosting/{created_hosting.id}/operations",
            json=operation_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["success"] is False
    
    def test_operation_on_nonexistent_hosting(self, client: TestClient, auth_headers):
        """존재하지 않는 호스팅에 대한 운영 명령 테스트"""
        operation_data = {"operation": "start"}
        non_existent_id = 99999
        response = client.post(
            f"/api/v1/hosting/{non_existent_id}/operations",
            json=operation_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert "호스팅을 찾을 수 없습니다" in data["message"]


class TestHostingPermissions:
    """호스팅 권한 테스트"""
    
    def test_access_other_user_hosting(self, client: TestClient, auth_headers_2, created_hosting):
        """다른 사용자의 호스팅에 접근 시도 테스트"""
        # created_hosting은 첫 번째 사용자의 것이고, auth_headers_2는 두 번째 사용자의 토큰
        response = client.get(f"/api/v1/hosting/{created_hosting.id}", headers=auth_headers_2)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["success"] is False
        assert "접근 권한이 없습니다" in data["message"]
    
    def test_operate_other_user_hosting(self, client: TestClient, auth_headers_2, created_hosting):
        """다른 사용자의 호스팅 운영 시도 테스트"""
        operation_data = {"operation": "start"}
        response = client.post(
            f"/api/v1/hosting/{created_hosting.id}/operations",
            json=operation_data,
            headers=auth_headers_2
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["success"] is False
        assert "접근 권한이 없습니다" in data["message"]


class TestHostingSync:
    """호스팅 동기화 테스트"""
    
    def test_sync_hosting_success(self, client: TestClient, auth_headers, created_hosting):
        """호스팅 상태 동기화 성공 테스트"""
        response = client.post(f"/api/v1/hosting/{created_hosting.id}/sync", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "동기화" in data["message"]
    
    def test_sync_nonexistent_hosting(self, client: TestClient, auth_headers):
        """존재하지 않는 호스팅 동기화 시도 테스트"""
        non_existent_id = 99999
        response = client.post(f"/api/v1/hosting/{non_existent_id}/sync", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False


class TestHostingStats:
    """호스팅 통계 테스트"""
    
    def test_get_hosting_stats_success(self, client: TestClient, auth_headers, created_hosting):
        """호스팅 통계 조회 성공 테스트"""
        response = client.get("/api/v1/hosting/stats", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        # 통계 데이터 구조 확인
        stats = data["data"]
        assert "total_hostings" in stats
        assert "active_hostings" in stats
        assert "status_breakdown" in stats
    
    def test_get_hosting_stats_unauthorized(self, client: TestClient):
        """인증 없이 호스팅 통계 조회 시도 테스트"""
        response = client.get("/api/v1/hosting/stats")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestHostingIntegration:
    """호스팅 통합 테스트"""
    
    def test_full_hosting_lifecycle(self, client: TestClient, auth_headers):
        """전체 호스팅 라이프사이클 테스트: 생성 -> 조회 -> 운영 -> 삭제"""
        
        # 1. 호스팅 생성
        create_response = client.post("/api/v1/host", json={}, headers=auth_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        hosting_data = create_response.json()
        hosting_id = hosting_data["data"]["id"]
        
        # 2. 호스팅 조회
        get_response = client.get(f"/api/v1/hosting/{hosting_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_200_OK
        
        # 3. 호스팅 시작
        start_data = {"operation": "start"}
        start_response = client.post(
            f"/api/v1/hosting/{hosting_id}/operations",
            json=start_data,
            headers=auth_headers
        )
        assert start_response.status_code == status.HTTP_200_OK
        
        # 4. 호스팅 중지
        stop_data = {"operation": "stop"}
        stop_response = client.post(
            f"/api/v1/hosting/{hosting_id}/operations",
            json=stop_data,
            headers=auth_headers
        )
        assert stop_response.status_code == status.HTTP_200_OK
        
        # 5. 호스팅 삭제
        delete_data = {"operation": "delete"}
        delete_response = client.post(
            f"/api/v1/hosting/{hosting_id}/operations",
            json=delete_data,
            headers=auth_headers
        )
        assert delete_response.status_code == status.HTTP_200_OK
    
    def test_multiple_user_hosting_isolation(self, client: TestClient, auth_headers, auth_headers_2):
        """여러 사용자 간 호스팅 격리 테스트"""
        
        # 첫 번째 사용자 호스팅 생성
        response1 = client.post("/api/v1/host", json={}, headers=auth_headers)
        assert response1.status_code == status.HTTP_201_CREATED
        hosting1_id = response1.json()["data"]["id"]
        
        # 두 번째 사용자 호스팅 생성
        response2 = client.post("/api/v1/host", json={}, headers=auth_headers_2)
        assert response2.status_code == status.HTTP_201_CREATED
        hosting2_id = response2.json()["data"]["id"]
        
        # 각 사용자는 자신의 호스팅만 조회 가능
        my_hosting1 = client.get("/api/v1/host", headers=auth_headers)
        assert my_hosting1.status_code == status.HTTP_200_OK
        assert my_hosting1.json()["data"]["id"] == hosting1_id
        
        my_hosting2 = client.get("/api/v1/host", headers=auth_headers_2)
        assert my_hosting2.status_code == status.HTTP_200_OK
        assert my_hosting2.json()["data"]["id"] == hosting2_id
        
        # 다른 사용자의 호스팅에는 접근 불가
        cross_access1 = client.get(f"/api/v1/hosting/{hosting2_id}", headers=auth_headers)
        assert cross_access1.status_code == status.HTTP_403_FORBIDDEN
        
        cross_access2 = client.get(f"/api/v1/hosting/{hosting1_id}", headers=auth_headers_2)
        assert cross_access2.status_code == status.HTTP_403_FORBIDDEN 