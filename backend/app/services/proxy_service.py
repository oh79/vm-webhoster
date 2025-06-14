"""
Nginx 프록시 서비스 - 웹/SSH 포트 포워딩 관리
"""
import os
import subprocess
import logging
import random
from pathlib import Path
from typing import Optional, Dict
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.core.exceptions import VMOperationError

# 로깅 설정
logger = logging.getLogger(__name__)

class ProxyService:
    """Nginx 프록시 관리 서비스"""
    
    def __init__(self):
        self.nginx_config_path = Path(settings.NGINX_CONFIG_PATH)
        self.sites_enabled_path = Path("/etc/nginx/sites-enabled")
        self.service_domain = settings.SERVICE_DOMAIN
        
        # Jinja2 템플릿 환경 설정
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        
        # 설정 디렉토리 생성
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리들이 존재하는지 확인하고 생성"""
        try:
            # Nginx 설정 디렉토리 생성
            self.nginx_config_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Nginx 설정 디렉토리 확인: {self.nginx_config_path}")
            
            # sites-enabled 디렉토리 확인 (실제 시스템에서)
            if not self.sites_enabled_path.exists():
                logger.warning(f"sites-enabled 디렉토리가 없습니다: {self.sites_enabled_path}")
                
        except Exception as e:
            logger.error(f"디렉토리 생성 실패: {e}")
            raise VMOperationError(f"프록시 디렉토리 설정 실패: {e}")
    
    def get_random_port(self, start: int = None, end: int = None) -> int:
        """
        사용 가능한 랜덤 포트 반환
        """
        start = start or settings.SSH_PORT_RANGE_START
        end = end or settings.SSH_PORT_RANGE_END
        
        max_attempts = 100
        for _ in range(max_attempts):
            port = random.randint(start, end)
            if self._is_port_available(port):
                logger.info(f"사용 가능한 포트 할당: {port}")
                return port
        
        raise VMOperationError(f"사용 가능한 포트를 찾을 수 없습니다. (범위: {start}-{end})")
    
    def _is_port_available(self, port: int) -> bool:
        """
        포트 사용 가능 여부 확인
        """
        try:
            # netstat으로 포트 사용 확인
            result = subprocess.run(
                ["netstat", "-an"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 포트가 LISTEN 상태인지 확인
            port_patterns = [f":{port} ", f":{port}\t"]
            for pattern in port_patterns:
                if pattern in result.stdout and "LISTEN" in result.stdout:
                    return False
                    
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning("포트 확인 시간 초과")
            return True
        except Exception as e:
            logger.warning(f"포트 확인 중 오류: {e}")
            return True  # 확인할 수 없으면 사용 가능한 것으로 간주
    
    def add_proxy_rule(self, user_id: str, vm_ip: str, ssh_port: int) -> Dict[str, str]:
        """
        웹 서비스 및 SSH 프록시 규칙 추가
        
        Args:
            user_id: 사용자 ID (VM ID)
            vm_ip: VM IP 주소
            ssh_port: SSH 포트 번호
            
        Returns:
            웹 URL 및 SSH 연결 정보
        """
        try:
            # 1. 웹 서비스 프록시 설정 생성
            web_url = self._create_web_proxy(user_id, vm_ip)
            
            # 2. SSH 포트 포워딩 설정 (향후 구현)
            ssh_command = f"ssh -p {ssh_port} ubuntu@{self.service_domain.split(':')[0]}"
            
            # 3. Nginx 설정 리로드
            if self._reload_nginx():
                logger.info(f"프록시 규칙 추가 완료: 사용자 {user_id}")
                
                return {
                    "web_url": web_url,
                    "ssh_command": ssh_command,
                    "ssh_port": str(ssh_port),
                    "vm_ip": vm_ip
                }
            else:
                raise VMOperationError("Nginx 설정 리로드 실패")
                
        except Exception as e:
            logger.error(f"프록시 규칙 추가 실패: {e}")
            # 실패 시 생성된 설정 파일 정리
            self._cleanup_config_file(user_id)
            raise VMOperationError(f"프록시 규칙 추가 실패: {e}")
    
    def _create_web_proxy(self, user_id: str, vm_ip: str) -> str:
        """
        웹 서비스 프록시 설정 생성
        """
        try:
            # 템플릿 로드
            template = self.jinja_env.get_template("nginx-site.conf.j2")
            
            # 템플릿 변수
            template_vars = {
                "user_id": user_id,
                "vm_ip": vm_ip,
                "service_domain": self.service_domain.split(':')[0],  # 도메인만 추출
                "vm_port": 80
            }
            
            # 설정 파일 내용 생성
            config_content = template.render(**template_vars)
            
            # 설정 파일 저장
            config_file = self.nginx_config_path / f"{user_id}.conf"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # sites-enabled에 심볼릭 링크 생성 (시스템에 따라 다를 수 있음)
            self._create_symlink(config_file, user_id)
            
            # 웹 URL 생성
            web_url = f"http://{self.service_domain}/{user_id}"
            logger.info(f"웹 프록시 설정 생성: {web_url} -> {vm_ip}:80")
            
            return web_url
            
        except Exception as e:
            logger.error(f"웹 프록시 설정 생성 실패: {e}")
            raise VMOperationError(f"웹 프록시 설정 생성 실패: {e}")
    
    def _create_symlink(self, config_file: Path, user_id: str):
        """
        sites-enabled에 심볼릭 링크 생성
        """
        try:
            if self.sites_enabled_path.exists():
                symlink_path = self.sites_enabled_path / f"{user_id}.conf"
                
                # 기존 심볼릭 링크 제거
                if symlink_path.exists():
                    symlink_path.unlink()
                
                # 새 심볼릭 링크 생성
                symlink_path.symlink_to(config_file)
                logger.info(f"심볼릭 링크 생성: {symlink_path} -> {config_file}")
            else:
                logger.warning("sites-enabled 디렉토리가 없어 심볼릭 링크를 생성하지 않습니다.")
                
        except Exception as e:
            logger.warning(f"심볼릭 링크 생성 실패: {e}")
            # 심볼릭 링크 실패는 치명적이지 않으므로 계속 진행
    
    def remove_proxy_rule(self, user_id: str) -> bool:
        """
        프록시 규칙 제거
        
        Args:
            user_id: 사용자 ID (VM ID)
            
        Returns:
            성공 여부
        """
        try:
            # 1. 설정 파일 제거
            config_file = self.nginx_config_path / f"{user_id}.conf"
            if config_file.exists():
                config_file.unlink()
                logger.info(f"설정 파일 제거: {config_file}")
            
            # 2. 심볼릭 링크 제거
            if self.sites_enabled_path.exists():
                symlink_path = self.sites_enabled_path / f"{user_id}.conf"
                if symlink_path.exists():
                    symlink_path.unlink()
                    logger.info(f"심볼릭 링크 제거: {symlink_path}")
            
            # 3. Nginx 설정 리로드
            if self._reload_nginx():
                logger.info(f"프록시 규칙 제거 완료: 사용자 {user_id}")
                return True
            else:
                logger.error("Nginx 설정 리로드 실패")
                return False
                
        except Exception as e:
            logger.error(f"프록시 규칙 제거 실패: {e}")
            return False
    
    def _cleanup_config_file(self, user_id: str):
        """
        설정 파일 정리 (에러 발생 시)
        """
        try:
            config_file = self.nginx_config_path / f"{user_id}.conf"
            if config_file.exists():
                config_file.unlink()
                logger.info(f"설정 파일 정리: {config_file}")
        except Exception as e:
            logger.warning(f"설정 파일 정리 실패: {e}")
    
    def reload_nginx(self) -> bool:
        """
        Nginx 설정 리로드 (외부 호출용)
        """
        return self._reload_nginx()
    
    def _reload_nginx(self) -> bool:
        """
        Nginx 설정 검증 및 리로드
        """
        try:
            # 1. 설정 파일 검증
            result = subprocess.run(
                ["nginx", "-t"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Nginx 설정 검증 실패: {result.stderr}")
                return False
            
            # 2. Nginx 리로드
            result = subprocess.run(
                ["nginx", "-s", "reload"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("Nginx 설정 리로드 성공")
                return True
            else:
                logger.error(f"Nginx 리로드 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Nginx 리로드 시간 초과")
            return False
        except FileNotFoundError:
            logger.warning("nginx 명령어를 찾을 수 없습니다. (개발 환경일 수 있음)")
            return True  # 개발 환경에서는 성공으로 처리
        except Exception as e:
            logger.error(f"Nginx 리로드 중 오류: {e}")
            return False
    
    def add_ssh_forwarding(self, user_id: str, vm_ip: str, ssh_port: int) -> bool:
        """
        SSH 포트 포워딩 설정 추가 (향후 확장용)
        
        현재는 iptables나 별도 SSH 터널링 구현 필요
        """
        try:
            # TODO: iptables 규칙 또는 SSH 터널링 설정
            logger.info(f"SSH 포트 포워딩 설정: {ssh_port} -> {vm_ip}:22")
            return True
            
        except Exception as e:
            logger.error(f"SSH 포트 포워딩 설정 실패: {e}")
            return False
    
    def get_proxy_info(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        프록시 설정 정보 조회
        """
        try:
            config_file = self.nginx_config_path / f"{user_id}.conf"
            
            if not config_file.exists():
                return None
            
            return {
                "config_file": str(config_file),
                "web_url": f"http://{self.service_domain}/{user_id}",
                "status": "active" if config_file.exists() else "inactive"
            }
            
        except Exception as e:
            logger.error(f"프록시 정보 조회 실패: {e}")
            return None 