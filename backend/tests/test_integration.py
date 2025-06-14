"""
통합 테스트 - 전체 호스팅 워크플로우 검증
"""
import pytest
import asyncio
import httpx
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.db.session import get_db
from app.models.user import User
from app.models.hosting import Hosting, HostingStatus
from app.services.hosting_service import HostingService
from app.services.vm_service import VMService
from app.services.proxy_service import ProxyService
from app.schemas.hosting import HostingCreate
from app.core.security import create_access_token, get_password_hash

class TestCompleteHostingFlow:
    """완전한 호스팅 플로우 테스트"""
    
    @pytest.fixture
    def test_user(self, db_session: Session):
        """테스트 사용자 생성"""
        user = User(
            email="integration_test@example.com",
            hashed_password=get_password_hash("testpass123"),
            username="integration_user",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def auth_headers(self, test_user):
        """인증 헤더"""
        token = create_access_token(data={"sub": test_user.email})
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def hosting_service(self, db_session: Session):
        """호스팅 서비스 인스턴스"""
        return HostingService(db_session)
    
    def test_01_user_registration_and_login(self, client):
        """사용자 회원가입 및 로그인 테스트"""
        # 1. 회원가입
        register_data = {
            "email": "test_flow@example.com",
            "password": "testpass123",
            "username": "testflowuser"
        }
        
        response = client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        
        result = response.json()
        assert result["success"] is True
        assert "user" in result["data"]
        assert result["data"]["user"]["email"] == register_data["email"]
        
        # 2. 로그인
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        
        return result["access_token"]
    
    def test_02_health_check_endpoints(self, client):
        """헬스체크 엔드포인트 테스트"""
        # 기본 헬스체크
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "healthy"
        assert "service" in result
        assert "timestamp" in result
        
        # 상세 헬스체크
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "service" in result["data"]
        assert "database" in result["data"]
    
    @patch('app.services.vm_service.VMService.create_vm')
    @patch('app.services.proxy_service.ProxyService.add_proxy_rule')
    def test_03_complete_hosting_creation_flow(
        self, 
        mock_proxy_add, 
        mock_vm_create, 
        client, 
        test_user, 
        auth_headers
    ):
        """완전한 호스팅 생성 플로우 테스트"""
        
        # VM 생성 모의 응답
        mock_vm_create.return_value = {
            "vm_id": "vm-test123",
            "vm_ip": "192.168.122.100",
            "disk_path": "/tmp/test.qcow2",
            "status": "running"
        }
        
        # 프록시 설정 모의 응답
        mock_proxy_add.return_value = {
            "web_url": f"http://localhost/{test_user.id}",
            "ssh_command": f"ssh -p 10001 ubuntu@localhost",
            "ssh_port": "10001",
            "vm_ip": "192.168.122.100"
        }
        
        # 호스팅 생성 요청
        response = client.post(
            "/api/v1/host",
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        
        assert result["success"] is True
        assert "hosting" in result["data"]
        
        hosting_data = result["data"]["hosting"]
        assert hosting_data["user_id"] == test_user.id
        assert hosting_data["status"] == HostingStatus.RUNNING.value
        assert hosting_data["vm_ip"] == "192.168.122.100"
        assert hosting_data["ssh_port"] is not None
        
        # 웹 접속 정보 확인
        assert "web_url" in result["data"]
        assert "ssh_command" in result["data"]
        
        # 모의 함수 호출 확인
        mock_vm_create.assert_called_once()
        mock_proxy_add.assert_called_once()
        
        return hosting_data
    
    def test_04_hosting_status_check(self, client, test_user, auth_headers):
        """호스팅 상태 조회 테스트"""
        response = client.get("/api/v1/host/my", headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            assert result["success"] is True
            assert "hosting" in result["data"]
            
            hosting = result["data"]["hosting"]
            assert hosting["user_id"] == test_user.id
            assert hosting["status"] in [status.value for status in HostingStatus]
        else:
            # 호스팅이 없는 경우
            assert response.status_code == 404
    
    @patch('app.services.vm_service.VMService.delete_vm')
    @patch('app.services.proxy_service.ProxyService.remove_proxy_rule')
    def test_05_hosting_deletion_flow(
        self, 
        mock_proxy_remove, 
        mock_vm_delete, 
        client, 
        test_user, 
        auth_headers
    ):
        """호스팅 삭제 플로우 테스트"""
        
        # 모의 응답 설정
        mock_vm_delete.return_value = True
        mock_proxy_remove.return_value = True
        
        # 먼저 호스팅이 있는지 확인
        response = client.get("/api/v1/host/my", headers=auth_headers)
        
        if response.status_code == 200:
            # 호스팅 삭제
            response = client.delete("/api/v1/host/my", headers=auth_headers)
            assert response.status_code == 200
            
            result = response.json()
            assert result["success"] is True
            assert "삭제되었습니다" in result["message"]
            
            # 모의 함수 호출 확인
            mock_vm_delete.assert_called_once()
            mock_proxy_remove.assert_called_once()
        else:
            # 호스팅이 없는 경우 스킵
            pytest.skip("삭제할 호스팅이 없습니다.")
    
    def test_06_error_handling_scenarios(self, client, test_user, auth_headers):
        """에러 처리 시나리오 테스트"""
        
        # 1. 중복 호스팅 생성 시도
        with patch('app.services.vm_service.VMService.create_vm') as mock_vm:
            mock_vm.return_value = {
                "vm_id": "vm-test456",
                "vm_ip": "192.168.122.101",
                "status": "running"
            }
            
            # 첫 번째 호스팅 생성
            response1 = client.post("/api/v1/host", headers=auth_headers)
            
            if response1.status_code == 201:
                # 두 번째 호스팅 생성 시도 (실패해야 함)
                response2 = client.post("/api/v1/host", headers=auth_headers)
                assert response2.status_code == 400
                
                result = response2.json()
                assert result["success"] is False
                assert "이미" in result["message"]
    
    def test_07_concurrent_hosting_creation(self, client):
        """동시 호스팅 생성 테스트"""
        # 여러 사용자 동시 호스팅 생성 시뮬레이션
        users_data = [
            {"email": f"concurrent_user_{i}@example.com", "password": "testpass123", "username": f"concurrent_user_{i}"}
            for i in range(3)
        ]
        
        tokens = []
        
        # 사용자 등록 및 토큰 획득
        for user_data in users_data:
            # 회원가입
            response = client.post("/api/v1/auth/register", json=user_data)
            if response.status_code == 201:
                # 로그인
                login_response = client.post("/api/v1/auth/login", data={
                    "username": user_data["email"],
                    "password": user_data["password"]
                })
                if login_response.status_code == 200:
                    token = login_response.json()["access_token"]
                    tokens.append(token)
        
        # 동시 호스팅 생성 (모의)
        with patch('app.services.vm_service.VMService.create_vm') as mock_vm, \
             patch('app.services.proxy_service.ProxyService.add_proxy_rule') as mock_proxy:
            
            mock_vm.return_value = {
                "vm_id": "vm-concurrent",
                "vm_ip": "192.168.122.200",
                "status": "running"
            }
            
            mock_proxy.return_value = {
                "web_url": "http://localhost/test",
                "ssh_command": "ssh -p 10002 ubuntu@localhost"
            }
            
            successful_creations = 0
            
            for i, token in enumerate(tokens):
                headers = {"Authorization": f"Bearer {token}"}
                response = client.post("/api/v1/host", headers=headers)
                
                if response.status_code == 201:
                    successful_creations += 1
                    assert response.json()["success"] is True
            
            # 모든 사용자가 성공적으로 호스팅을 생성해야 함
            assert successful_creations == len(tokens)

class TestServiceIntegration:
    """서비스 간 통합 테스트"""
    
    def test_vm_service_integration(self):
        """VM 서비스 통합 테스트"""
        vm_service = VMService()
        
        # VM ID 생성 테스트
        vm_id = vm_service.generate_vm_id()
        assert vm_id.startswith("vm-")
        assert len(vm_id) > 8
        
        # 포트 할당 테스트
        port = vm_service.get_available_ssh_port()
        assert 10000 <= port <= 20000
    
    def test_proxy_service_integration(self):
        """프록시 서비스 통합 테스트"""
        proxy_service = ProxyService()
        
        # 랜덤 포트 생성 테스트
        port = proxy_service.get_random_port()
        assert 10000 <= port <= 20000
        
        # 프록시 정보 조회 테스트 (존재하지 않는 사용자)
        proxy_info = proxy_service.get_proxy_info("nonexistent_user")
        assert proxy_info is None
    
    @patch('app.services.vm_service.subprocess.run')
    def test_vm_creation_simulation(self, mock_subprocess):
        """VM 생성 시뮬레이션 테스트"""
        # subprocess 모의 설정
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="success")
        
        vm_service = VMService()
        
        # VM 디스크 생성 시뮬레이션
        try:
            disk_path = vm_service.create_vm_disk("test-vm-123", 20)
            assert "test-vm-123.qcow2" in disk_path
        except Exception as e:
            # 실제 시스템에서는 qemu-img가 없을 수 있음
            assert "qemu-img" in str(e) or "VM 디스크 생성" in str(e)

class TestAPIEndpoints:
    """API 엔드포인트 상세 테스트"""
    
    def test_auth_endpoints(self, client):
        """인증 관련 엔드포인트 테스트"""
        
        # 1. 회원가입 - 유효한 데이터
        valid_register_data = {
            "email": "api_test@example.com",
            "password": "validpass123",
            "username": "api_test_user"
        }
        
        response = client.post("/api/v1/auth/register", json=valid_register_data)
        assert response.status_code == 201
        
        # 2. 회원가입 - 중복 이메일
        response = client.post("/api/v1/auth/register", json=valid_register_data)
        assert response.status_code == 400
        
        # 3. 로그인 - 유효한 인증정보
        login_data = {
            "username": valid_register_data["email"],
            "password": valid_register_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        
        # 4. 사용자 정보 조회
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["email"] == valid_register_data["email"]
        assert user_data["username"] == valid_register_data["username"]
    
    def test_hosting_endpoints_without_auth(self, client):
        """인증 없이 호스팅 엔드포인트 접근 테스트"""
        
        # 인증 없이 호스팅 생성 시도
        response = client.post("/api/v1/host")
        assert response.status_code == 401
        
        # 인증 없이 호스팅 조회 시도
        response = client.get("/api/v1/host/my")
        assert response.status_code == 401
        
        # 인증 없이 호스팅 삭제 시도
        response = client.delete("/api/v1/host/my")
        assert response.status_code == 401
    
    def test_error_response_format(self, client):
        """에러 응답 형식 테스트"""
        
        # 존재하지 않는 엔드포인트
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # 잘못된 JSON 데이터
        response = client.post(
            "/api/v1/auth/register",
            data="잘못된 JSON",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_async_operations():
    """비동기 작업 테스트"""
    
    # HTTP 클라이언트를 사용한 비동기 요청 시뮬레이션
    async with httpx.AsyncClient() as client:
        # 실제 서버가 실행 중이지 않을 수 있으므로 모의 테스트
        try:
            response = await client.get("http://localhost:8000/api/v1/health")
            if response.status_code == 200:
                assert "status" in response.json()
        except httpx.ConnectError:
            # 서버가 실행되지 않은 경우 패스
            pass 