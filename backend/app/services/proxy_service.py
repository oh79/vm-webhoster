"""
프록시 서비스 - Nginx 리버스 프록시 관리 (리팩토링 버전)
"""
import os
import subprocess
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from jinja2 import Template

from app.core.config import settings
from app.utils.logging_utils import get_logger

logger = get_logger("proxy_service")

class ProxyService:
    """
    Nginx 리버스 프록시 관리 서비스 (리팩토링 버전)
    
    새로운 구조:
    - 모듈화된 nginx 설정
    - Jinja2 템플릿 시스템
    - 통합된 설정 관리
    - 자동 백업 및 롤백
    """
    
    def __init__(self):
        # 프로젝트 nginx 디렉토리 (개발용)
        self.project_nginx_dir = Path(settings.PROJECT_ROOT) / "nginx"
        
        # 시스템 nginx 디렉토리 (운영용)
        self.nginx_dir = Path("/etc/nginx")
        self.hosting_dir = self.nginx_dir / "sites-available" / "hosting"
        
        # 템플릿 파일 경로
        self.template_file = self.project_nginx_dir / "templates" / "user-hosting.conf.j2"
        
        # nginx 관리 스크립트
        self.manager_script = Path(settings.PROJECT_ROOT) / "scripts" / "nginx-config-manager.sh"
        
        # 설정 검증
        self._validate_setup()
    
    def _validate_setup(self) -> None:
        """초기 설정 검증"""
        try:
            # 디렉토리 생성
            self.hosting_dir.mkdir(parents=True, exist_ok=True)
            
            # 템플릿 파일 확인
            if not self.template_file.exists():
                logger.warning(f"템플릿 파일이 없습니다: {self.template_file}")
            
            # 관리 스크립트 확인
            if not self.manager_script.exists():
                logger.warning(f"관리 스크립트가 없습니다: {self.manager_script}")
            else:
                # 실행 권한 확인
                self.manager_script.chmod(0o755)
                
        except Exception as e:
            logger.error(f"프록시 서비스 초기화 실패: {e}")
    
    def add_proxy_rule(
        self, 
        user_id: str, 
        vm_ip: str, 
        ssh_port: int,
        web_port: int = 80,
        vm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자 호스팅 프록시 규칙 추가 (개선된 버전 - 검증 및 자동 복구 포함)
        
        Args:
            user_id: 사용자 ID
            vm_ip: VM IP 주소
            ssh_port: SSH 포트
            web_port: 웹 포트 (기본값: 80)
            vm_id: VM ID (선택사항)
        
        Returns:
            프록시 설정 결과 정보
        """
        try:
            logger.info(f"프록시 규칙 추가 시작: 사용자 {user_id}, IP: {vm_ip}, 웹포트: {web_port}")
            
            # VM ID 기본값 설정
            if not vm_id:
                vm_id = f"vm-{user_id}"
            
            # 컨테이너 연결 사전 테스트
            if not self._test_vm_connection(vm_ip, web_port):
                logger.warning(f"VM 연결 테스트 실패: {vm_ip}:{web_port}, 계속 진행...")
            
            # nginx 관리 스크립트를 sudo 권한으로 실행
            cmd = [
                "sudo",
                str(self.manager_script),
                "add-user", user_id,
                "--vm-id", vm_id,
                "--vm-ip", vm_ip,
                "--web-port", str(web_port),
                "--ssh-port", str(ssh_port),
                "--force"  # 기존 설정 덮어쓰기
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"설정 추가 완료: {result.stdout}")
            
            # Nginx 설정 검증 (sudo 권한으로)
            if not self._validate_nginx_config_with_sudo():
                logger.error("Nginx 설정 검증 실패")
                raise Exception("생성된 nginx 설정에 오류가 있습니다")
            
            # Nginx 설정 리로드
            self._reload_nginx()
            
            # 설정 적용 후 검증 (최대 30초 대기)
            proxy_working = False
            for i in range(30):
                time.sleep(1)
                if self._test_proxy_rule(user_id, vm_ip, web_port):
                    proxy_working = True
                    logger.info(f"프록시 규칙 검증 성공: 사용자 {user_id}")
                    break
            
            if not proxy_working:
                logger.warning(f"프록시 규칙 검증 실패: 사용자 {user_id}, 자동 복구 시도...")
                # 자동 복구 시도
                if self._auto_fix_proxy_rule(user_id, vm_ip, web_port, ssh_port, vm_id):
                    logger.info(f"프록시 규칙 자동 복구 성공: 사용자 {user_id}")
                    proxy_working = True
                else:
                    logger.error(f"프록시 규칙 자동 복구 실패: 사용자 {user_id}")
            
            # 결과 정보 생성
            proxy_info = {
                "user_id": user_id,
                "vm_id": vm_id,
                "vm_ip": vm_ip,
                "web_port": web_port,
                "ssh_port": ssh_port,
                "web_url": f"http://localhost/{user_id}",
                "ssh_command": f"ssh -p {ssh_port} ubuntu@localhost",
                "sftp_command": f"sftp -P {ssh_port} ubuntu@localhost",
                "config_file": str(self.hosting_dir / f"{user_id}.conf"),
                "status": "active" if proxy_working else "warning",
                "verified": proxy_working,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"프록시 규칙 추가 완료: 사용자 {user_id}, 검증: {'성공' if proxy_working else '실패'}")
            return proxy_info
            
        except subprocess.CalledProcessError as e:
            logger.error(f"프록시 규칙 추가 실패: {e.stderr}")
            raise Exception(f"nginx 설정 추가 실패: {e.stderr}")
        except Exception as e:
            logger.error(f"프록시 규칙 추가 오류: {e}")
            raise
    
    def _test_vm_connection(self, vm_ip: str, web_port: int, timeout: int = 5) -> bool:
        """
        VM 연결 테스트
        
        Args:
            vm_ip: VM IP 주소
            web_port: 웹 포트
            timeout: 타임아웃 (초)
        
        Returns:
            연결 성공 여부
        """
        try:
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((vm_ip, web_port))
            sock.close()
            
            return result == 0
            
        except Exception as e:
            logger.error(f"VM 연결 테스트 오류: {e}")
            return False
    
    def _test_proxy_rule(self, user_id: str, vm_ip: str, web_port: int) -> bool:
        """
        프록시 규칙 동작 테스트
        
        Args:
            user_id: 사용자 ID
            vm_ip: VM IP 주소
            web_port: 웹 포트
        
        Returns:
            프록시 동작 여부
        """
        try:
            import requests
            
            # 로컬 프록시 URL 테스트
            proxy_url = f"http://localhost/{user_id}"
            
            response = requests.get(proxy_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"프록시 규칙 테스트 성공: {proxy_url}")
                return True
            else:
                logger.warning(f"프록시 규칙 테스트 실패: {proxy_url} (상태코드: {response.status_code})")
                return False
                
        except Exception as e:
            logger.error(f"프록시 규칙 테스트 오류: {e}")
            return False
    
    def _validate_nginx_config_with_sudo(self) -> bool:
        """
        Nginx 설정 검증 (sudo 권한으로)
        
        Returns:
            설정 유효성 여부
        """
        try:
            cmd = ["sudo", str(self.manager_script), "validate"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Nginx 설정 검증 오류: {e}")
            return False

    def validate_nginx_config(self) -> bool:
        """
        Nginx 설정 검증 (공개 메서드)
        
        Returns:
            설정 유효성 여부
        """
        return self._validate_nginx_config_with_sudo()
    
    def _auto_fix_proxy_rule(self, user_id: str, vm_ip: str, web_port: int, ssh_port: int, vm_id: str) -> bool:
        """
        프록시 규칙 자동 복구
        
        Args:
            user_id: 사용자 ID
            vm_ip: VM IP 주소
            web_port: 웹 포트
            ssh_port: SSH 포트
            vm_id: VM ID
        
        Returns:
            복구 성공 여부
        """
        try:
            logger.info(f"프록시 규칙 자동 복구 시작: 사용자 {user_id}")
            
            # 1. 기존 설정 제거
            self.remove_proxy_rule(user_id)
            
            # 2. 잠시 대기
            time.sleep(2)
            
            # 3. 새로운 설정 추가 (재귀 호출 방지를 위해 간단한 버전)
            cmd = [
                "sudo",
                str(self.manager_script),
                "add-user", user_id,
                "--vm-id", vm_id,
                "--vm-ip", vm_ip,
                "--web-port", str(web_port),
                "--ssh-port", str(ssh_port),
                "--force"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 4. nginx 리로드
            self._reload_nginx()
            
            # 5. 복구 검증
            time.sleep(3)
            if self._test_proxy_rule(user_id, vm_ip, web_port):
                logger.info(f"프록시 규칙 자동 복구 성공: 사용자 {user_id}")
                return True
            else:
                logger.error(f"프록시 규칙 자동 복구 검증 실패: 사용자 {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"프록시 규칙 자동 복구 오류: {e}")
            return False
    
    def remove_proxy_rule(self, user_id: str) -> bool:
        """
        사용자 호스팅 프록시 규칙 제거
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            제거 성공 여부
        """
        try:
            logger.info(f"프록시 규칙 제거 시작: 사용자 {user_id}")
            
            # nginx 관리 스크립트를 sudo 권한으로 실행
            cmd = [
                "sudo",
                str(self.manager_script),
                "remove-user", user_id
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"설정 제거 완료: {result.stdout}")
            
            # Nginx 설정 리로드
            self._reload_nginx()
            
            logger.info(f"프록시 규칙 제거 완료: 사용자 {user_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"프록시 규칙 제거 실패: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"프록시 규칙 제거 오류: {e}")
            return False
    
    def update_proxy_rule(
        self, 
        user_id: str, 
        vm_ip: str, 
        ssh_port: int,
        web_port: int = 80,
        vm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자 호스팅 프록시 규칙 업데이트
        
        Args:
            user_id: 사용자 ID
            vm_ip: VM IP 주소  
            ssh_port: SSH 포트
            web_port: 웹 포트
            vm_id: VM ID
        
        Returns:
            업데이트된 프록시 설정 정보
        """
        try:
            logger.info(f"프록시 규칙 업데이트 시작: 사용자 {user_id}")
            
            # 기존 규칙 제거 후 새로 추가
            return self.add_proxy_rule(user_id, vm_ip, ssh_port, web_port, vm_id)
            
        except Exception as e:
            logger.error(f"프록시 규칙 업데이트 오류: {e}")
            raise
    
    def get_proxy_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        사용자 프록시 설정 정보 조회
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            프록시 설정 정보 또는 None
        """
        try:
            config_file = self.hosting_dir / f"{user_id}.conf"
            
            if not config_file.exists():
                return None
            
            # 설정 파일에서 정보 추출
            config_content = config_file.read_text()
            
            # 간단한 파싱 (정규식 사용 가능)
            vm_id = self._extract_from_config(config_content, "# VM ID: (.+)")
            web_port = self._extract_from_config(config_content, r"proxy_pass http://[^:]+:(\d+)")
            ssh_port = self._extract_from_config(config_content, r"ssh -p (\d+)")
            vm_ip = self._extract_from_config(config_content, r"proxy_pass http://([^:]+):")
            
            return {
                "user_id": user_id,
                "vm_id": vm_id,
                "vm_ip": vm_ip or "127.0.0.1",
                "web_port": int(web_port) if web_port else 80,
                "ssh_port": int(ssh_port) if ssh_port else None,
                "web_url": f"http://localhost/{user_id}",
                "ssh_command": f"ssh -p {ssh_port} ubuntu@localhost" if ssh_port else None,
                "config_file": str(config_file),
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"프록시 정보 조회 오류: {e}")
            return None
    
    def list_proxy_rules(self) -> Dict[str, Any]:
        """
        모든 프록시 규칙 목록 조회
        
        Returns:
            프록시 규칙 목록 정보
        """
        try:
            # nginx 관리 스크립트를 사용하여 사용자 목록 조회
            cmd = [str(self.manager_script), "list-users"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 결과 파싱
            users = []
            for line in result.stdout.split('\n'):
                if '사용자 ID:' in line:
                    # 예: "  • 사용자 ID: 7 (VM: vm-abc123)"
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        user_id = parts[3]
                        vm_id = parts[5].strip('()') if len(parts) > 5 else "N/A"
                        users.append({
                            "user_id": user_id,
                            "vm_id": vm_id
                        })
            
            return {
                "total_users": len(users),
                "users": users,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"프록시 규칙 목록 조회 오류: {e}")
            return {
                "total_users": 0,
                "users": [],
                "status": "error",
                "error": str(e)
            }
    
    def get_nginx_status(self) -> Dict[str, Any]:
        """
        Nginx 서비스 상태 조회
        
        Returns:
            Nginx 상태 정보
        """
        try:
            cmd = [str(self.manager_script), "status"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "status": "running" if "실행 중" in result.stdout else "stopped",
                "config_valid": self.validate_nginx_config(),
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Nginx 상태 조회 오류: {e}")
            return {
                "status": "unknown",
                "config_valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup_old_configs(self) -> Dict[str, Any]:
        """
        이전 버전의 nginx 설정 파일들 정리
        
        Returns:
            정리 결과 정보
        """
        try:
            logger.info("이전 nginx 설정 파일 정리 시작")
            
            cmd = [str(self.manager_script), "cleanup", "--backup"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"정리 완료: {result.stdout}")
            
            return {
                "status": "success",
                "message": "이전 설정 파일들이 정리되었습니다",
                "output": result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"설정 파일 정리 실패: {e.stderr}")
            return {
                "status": "error",
                "message": "설정 파일 정리 중 오류가 발생했습니다",
                "error": e.stderr
            }
        except Exception as e:
            logger.error(f"설정 파일 정리 오류: {e}")
            return {
                "status": "error",
                "message": "설정 파일 정리 중 예상치 못한 오류가 발생했습니다",
                "error": str(e)
            }
    
    def migrate_from_old_structure(self) -> Dict[str, Any]:
        """
        기존 구조에서 새 구조로 마이그레이션
        
        Returns:
            마이그레이션 결과 정보
        """
        try:
            logger.info("nginx 설정 마이그레이션 시작")
            
            cmd = [str(self.manager_script), "migrate", "--backup"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"마이그레이션 완료: {result.stdout}")
            
            return {
                "status": "success",
                "message": "nginx 설정 마이그레이션이 완료되었습니다",
                "output": result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"마이그레이션 실패: {e.stderr}")
            return {
                "status": "error",
                "message": "마이그레이션 중 오류가 발생했습니다",
                "error": e.stderr
            }
        except Exception as e:
            logger.error(f"마이그레이션 오류: {e}")
            return {
                "status": "error", 
                "message": "마이그레이션 중 예상치 못한 오류가 발생했습니다",
                "error": str(e)
            }
    
    def _extract_from_config(self, content: str, pattern: str) -> Optional[str]:
        """설정 파일에서 패턴 매칭하여 값 추출"""
        import re
        match = re.search(pattern, content)
        return match.group(1) if match else None
    
    def _reload_nginx(self) -> None:
        """Nginx 설정 리로드"""
        try:
            # 개발 환경에서도 nginx 리로드 실행 (sudo 권한으로)
            cmd = ["sudo", str(self.manager_script), "reload"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Nginx 리로드 완료")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Nginx 리로드 실패: {e.stderr}")
            raise Exception(f"Nginx 리로드 실패: {e.stderr}")
    
    def _ensure_nginx_running(self) -> bool:
        """Nginx 서비스 실행 확인 및 시작"""
        try:
            # 서비스 상태 확인
            result = subprocess.run(
                ["systemctl", "is-active", "nginx"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True
            
            # 서비스 시작 시도
            subprocess.run(
                ["systemctl", "start", "nginx"],
                check=True
            )
            
            logger.info("Nginx 서비스 시작 완료")
            return True
            
        except Exception as e:
            logger.error(f"Nginx 서비스 시작 실패: {e}")
            return False 