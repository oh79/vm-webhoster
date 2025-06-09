"""
헬스체크 API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestHealthCheck:
    """헬스체크 테스트"""
    
    def test_basic_health_check(self, client: TestClient):
        """기본 헬스체크 테스트"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "웹 호스팅 서비스"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
    
    def test_detailed_health_check(self, client: TestClient):
        """상세 헬스체크 테스트"""
        response = client.get("/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        health_data = data["data"]
        assert "service" in health_data
        assert "database" in health_data
        assert "environment" in health_data
        
        # 서비스 정보 확인
        service_info = health_data["service"]
        assert service_info["status"] == "healthy"
        assert service_info["name"] == "웹 호스팅 서비스"
        assert service_info["version"] == "1.0.0"
        
        # 데이터베이스 상태 확인
        db_info = health_data["database"]
        assert db_info["status"] == "healthy"
        assert db_info["error"] is None
    
    def test_version_info(self, client: TestClient):
        """버전 정보 테스트"""
        response = client.get("/version")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        version_data = data["data"]
        assert "version" in version_data
        assert "service_name" in version_data
        assert "description" in version_data
        assert version_data["version"] == "1.0.0"
        assert version_data["service_name"] == "웹 호스팅 서비스"
    
    def test_ping_endpoint(self, client: TestClient):
        """핑 엔드포인트 테스트"""
        response = client.get("/ping")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "pong"
        assert "timestamp" in data


class TestApplicationRoot:
    """애플리케이션 루트 엔드포인트 테스트"""
    
    def test_root_endpoint(self, client: TestClient):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "description" in data
        assert "status" in data
        assert data["status"] == "running"
        assert data["api_prefix"] == "/api/v1"
    
    def test_favicon_endpoint(self, client: TestClient):
        """파비콘 엔드포인트 테스트"""
        response = client.get("/favicon.ico")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT 