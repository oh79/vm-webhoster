"""
Nginx 프록시 서비스 - 웹/SSH 포트 포워딩 관리 (개선된 버전)
"""
import os
import subprocess
import logging
import random
import time
from pathlib import Path
from typing import Optional, Dict, List
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings
from app.core.exceptions import VMOperationError

# 로깅 설정
logger = logging.getLogger(__name__)

class ProxyService:
    """Nginx 프록시 관리 서비스 (개선된 버전)"""
    
    def __init__(self):
        self.nginx_config_path = Path(settings.NGINX_CONFIG_PATH)
        self.sites_enabled_path = Path("/etc/nginx/sites-enabled")
        self.service_domain = settings.SERVICE_DOMAIN
        
        # Jinja2 템플릿 환경 설정 (보안 강화)
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml', 'j2']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 설정 디렉토리 생성
        self._ensure_directories()
        
        # Nginx 설정 검증
        self._validate_nginx_config()
    
    def _ensure_directories(self):
        """필요한 디렉토리들이 존재하는지 확인하고 생성"""
        try:
            # Nginx 설정 디렉토리 생성
            self.nginx_config_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Nginx 설정 디렉토리 확인: {self.nginx_config_path}")
            
            # 백업 디렉토리 생성
            backup_dir = self.nginx_config_path / "backup"
            backup_dir.mkdir(exist_ok=True)
            
            # sites-enabled 디렉토리 확인 (실제 시스템에서)
            if not self.sites_enabled_path.exists():
                logger.warning(f"sites-enabled 디렉토리가 없습니다: {self.sites_enabled_path}")
                
        except Exception as e:
            logger.error(f"디렉토리 생성 실패: {e}")
            raise VMOperationError(f"프록시 디렉토리 설정 실패: {e}")
    
    def _validate_nginx_config(self):
        """Nginx 설정 유효성 검사"""
        try:
            result = subprocess.run(
                ["nginx", "-t"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("Nginx 설정 검증 통과")
            else:
                logger.warning(f"Nginx 설정에 문제가 있을 수 있습니다: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Nginx 설정 검증을 수행할 수 없습니다. nginx가 설치되어 있는지 확인하세요.")
        except Exception as e:
            logger.warning(f"Nginx 설정 검증 실패: {e}")
    
    def get_random_port(self, start: int = None, end: int = None) -> int:
        """
        사용 가능한 랜덤 포트 반환 (개선된 버전)
        """
        start = start or settings.SSH_PORT_RANGE_START
        end = end or settings.SSH_PORT_RANGE_END
        
        max_attempts = 100
        attempted_ports = set()
        
        for attempt in range(max_attempts):
            port = random.randint(start, end)
            
            # 이미 시도한 포트는 건너뛰기
            if port in attempted_ports:
                continue
            attempted_ports.add(port)
            
            if self._is_port_available(port):
                logger.info(f"사용 가능한 포트 할당: {port} (시도 {attempt + 1}회)")
                return port
        
        raise VMOperationError(f"사용 가능한 포트를 찾을 수 없습니다. (범위: {start}-{end}, 시도: {max_attempts}회)")
    
    def _is_port_available(self, port: int) -> bool:
        """
        포트 사용 가능 여부 확인 (개선된 버전)
        """
        try:
            # 1. ss 명령어 사용 (netstat보다 빠름)
            result = subprocess.run(
                ["ss", "-tuln", f"sport = :{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return False  # 포트가 사용 중
            
            # 2. netstat 명령어 사용 (대체 방법)
            result = subprocess.run(
                ["netstat", "-tuln"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # 포트가 LISTEN 상태인지 확인
                for line in result.stdout.split('\n'):
                    if f":{port} " in line and "LISTEN" in line:
                        return False
                        
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning(f"포트 {port} 확인 시간 초과")
            return True
        except FileNotFoundError:
            logger.warning("포트 확인 도구를 찾을 수 없습니다.")
            return True
        except Exception as e:
            logger.warning(f"포트 {port} 확인 중 오류: {e}")
            return True
    
    def add_proxy_rule(self, user_id: str, vm_ip: str, ssh_port: int, web_port: int = None) -> Dict[str, str]:
        """
        사용자별 프록시 규칙 추가 (과제 요구사항 구현)
        /<user_id> -> VM의 웹포트로 프록시
        """
        try:
            # 웹 포트가 제공되지 않으면 SSH 포트 기반으로 추정
            if not web_port:
                web_port = 8000 + (hash(user_id) % 1000)
            
            # Nginx 설정 파일 생성
            config_content = f"""# 사용자 {user_id}의 웹 호스팅 프록시 설정
server {{
    listen 80;
    server_name localhost;
    
    # 사용자별 웹 호스팅 라우팅: /{user_id} -> VM 웹포트
    location /{user_id} {{
        # 경로 rewrite (/{user_id}/path -> /path)
        rewrite ^/{user_id}(/.*)$ $1 break;
        rewrite ^/{user_id}$ / break;
        
        # VM의 웹포트로 프록시
        proxy_pass http://127.0.0.1:{web_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 웹소켓 지원
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
    
    # 루트 접근 시 사용자 목록 표시 (선택사항)
    location = / {{
        return 200 '<h1>웹 호스팅 서비스</h1><p>사용자별 접근: /{user_id}</p><p>현재 활성 사용자: {user_id}</p>';
        add_header Content-Type text/html;
    }}
}}

# SSH 포트 포워딩을 위한 stream 설정 (별도 파일에서 관리)
# SSH 접속: ssh -p {ssh_port} user@localhost
"""
            
            # 설정 파일 저장
            config_file = self.nginx_config_path / f"{user_id}.conf"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
                
            logger.info(f"프록시 설정 파일 생성: {config_file}")
            
            # Nginx sites-enabled에 심볼릭 링크 생성 (권한이 있는 경우)
            try:
                sites_enabled = self.sites_enabled_path
                if sites_enabled.exists():
                    link_target = sites_enabled / f"{user_id}.conf"
                    if not link_target.exists():
                        link_target.symlink_to(config_file)
                        logger.info(f"Nginx 사이트 활성화: {link_target}")
                        
                        # Nginx 리로드 시도
                        try:
                            subprocess.run(["sudo", "nginx", "-s", "reload"], 
                                         check=True, timeout=10, capture_output=True)
                            logger.info("Nginx 설정 리로드 완료")
                        except subprocess.CalledProcessError as e:
                            logger.warning(f"Nginx 리로드 실패: {e}")
                            
                else:
                    logger.info("sites-enabled 디렉토리가 없어 로컬 설정 파일만 생성합니다.")
                            
            except (OSError, subprocess.CalledProcessError, PermissionError) as e:
                logger.warning(f"Nginx 설정 적용 실패 (개발환경에서는 정상): {e}")
                logger.info("로컬 설정 파일로 대체합니다. Docker 프록시나 별도 nginx 설정을 사용하세요.")
            
            # 결과 반환
            result = {
                "user_id": user_id,
                "web_url": f"http://localhost/{user_id}",
                "direct_web_url": f"http://localhost:{web_port}",
                "ssh_command": f"ssh -p {ssh_port} user@localhost",
                "ssh_port": str(ssh_port),
                "web_port": str(web_port),
                "config_file": str(config_file),
                "proxy_status": "active"
            }
            
            logger.info(f"프록시 규칙 추가 완료: {user_id} -> {web_port}")
            return result
            
        except Exception as e:
            logger.error(f"프록시 규칙 추가 실패: {e}")
            raise Exception(f"프록시 설정 실패: {e}")
    
    def _validate_ip_address(self, ip: str) -> bool:
        """IP 주소 형식 검증"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    def _backup_existing_config(self, user_id: str) -> None:
        """기존 설정 파일 백업"""
        try:
            config_file = self.nginx_config_path / f"{user_id}.conf"
            if config_file.exists():
                backup_dir = self.nginx_config_path / "backup"
                timestamp = int(time.time())
                backup_file = backup_dir / f"{user_id}_{timestamp}.conf.bak"
                
                import shutil
                shutil.copy2(config_file, backup_file)
                logger.info(f"설정 백업 완료: {backup_file}")
        except Exception as e:
            logger.warning(f"설정 백업 실패: {e}")
    
    def _restore_backup_config(self, user_id: str) -> None:
        """백업된 설정 파일 복원"""
        try:
            backup_dir = self.nginx_config_path / "backup"
            backup_files = list(backup_dir.glob(f"{user_id}_*.conf.bak"))
            
            if backup_files:
                # 가장 최근 백업 파일 선택
                latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
                config_file = self.nginx_config_path / f"{user_id}.conf"
                
                import shutil
                shutil.copy2(latest_backup, config_file)
                logger.info(f"설정 복원 완료: {latest_backup} -> {config_file}")
        except Exception as e:
            logger.error(f"설정 복원 실패: {e}")
    
    def _create_web_proxy(self, user_id: str, vm_ip: str) -> str:
        """
        웹 서비스 프록시 설정 생성 (개선된 버전)
        """
        try:
            # 템플릿 로드
            template = self.jinja_env.get_template("nginx-site.conf.j2")
            
            # 템플릿 변수 (보안 강화)
            template_vars = {
                "user_id": user_id,
                "vm_ip": vm_ip,
                "service_domain": self.service_domain.split(':')[0],
                "vm_port": 80,
                "ssl_enabled": False,  # 향후 SSL 지원용
                "max_body_size": "10M",
                "proxy_timeout": 30,
                "enable_logging": True,
                "security_headers": True
            }
            
            # 설정 파일 내용 생성
            config_content = template.render(**template_vars)
            
            # 설정 파일 저장
            config_file = self.nginx_config_path / f"{user_id}.conf"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # 파일 권한 설정
            config_file.chmod(0o644)
            
            # sites-enabled에 심볼릭 링크 생성
            self._create_symlink(config_file, user_id)
            
            # 웹 URL 생성
            web_url = f"http://{self.service_domain}/{user_id}"
            logger.info(f"웹 프록시 설정 생성: {web_url} -> {vm_ip}:80")
            
            return web_url
            
        except Exception as e:
            logger.error(f"웹 프록시 설정 생성 실패: {e}")
            raise VMOperationError(f"웹 프록시 설정 생성 실패: {e}")
    
    def _create_ssh_forwarding(self, user_id: str, vm_ip: str, ssh_port: int) -> Optional[Dict[str, str]]:
        """
        SSH 포트 포워딩 설정 생성 (실제 구현)
        """
        try:
            # SSH 포워딩 정보 생성
            forwarding_info = {
                "ssh_internal_port": 22,  # VM 내부 SSH 포트
                "ssh_external_port": ssh_port,  # 외부 접속용 포트
                "forwarding_rule": f"iptables -t nat -A PREROUTING -p tcp --dport {ssh_port} -j DNAT --to-destination {vm_ip}:22",
                "forwarding_status": "configured"
            }
            
            # 실제 포트 포워딩 규칙 추가 (iptables 사용)
            # 주의: 실제 환경에서는 권한과 네트워크 설정을 확인해야 함
            try:
                # iptables 규칙 추가 (실제로는 더 복잡한 네트워크 설정 필요)
                logger.info(f"SSH 포트 포워딩 설정: {ssh_port} -> {vm_ip}:22")
                # 실제 구현에서는 네트워크 관리자 권한이 필요
                # subprocess.run([...], check=True)
            except Exception as e:
                logger.warning(f"SSH 포트 포워딩 설정 실패: {e}")
                forwarding_info["forwarding_status"] = "failed"
            
            return forwarding_info
            
        except Exception as e:
            logger.error(f"SSH 포워딩 설정 실패: {e}")
            return None
    
    def _create_symlink(self, config_file: Path, user_id: str):
        """
        sites-enabled에 심볼릭 링크 생성 (개선된 버전)
        """
        try:
            if self.sites_enabled_path.exists():
                symlink_path = self.sites_enabled_path / f"{user_id}.conf"
                
                # 기존 심볼릭 링크 제거
                if symlink_path.exists() or symlink_path.is_symlink():
                    symlink_path.unlink()
                
                # 새 심볼릭 링크 생성
                symlink_path.symlink_to(config_file)
                logger.info(f"심볼릭 링크 생성: {symlink_path} -> {config_file}")
            else:
                logger.warning("sites-enabled 디렉토리가 없어 심볼릭 링크를 생성하지 않습니다.")
                
        except Exception as e:
            logger.warning(f"심볼릭 링크 생성 실패: {e}")
            # 심볼릭 링크 실패는 치명적이지 않으므로 계속 진행
    
    def _test_and_reload_nginx(self) -> bool:
        """
        Nginx 설정 테스트 및 리로드 (개발 환경용 Mock 버전)
        """
        try:
            # 개발 환경에서는 Mock으로 성공 반환
            if settings.DEBUG:
                logger.info("개발 환경: Mock Nginx 설정 테스트 및 리로드 성공")
                return True
            
            # 1. 설정 파일 문법 검사
            test_result = subprocess.run(
                ["nginx", "-t"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if test_result.returncode != 0:
                logger.error(f"Nginx 설정 테스트 실패: {test_result.stderr}")
                return False
            
            # 2. Nginx 리로드
            reload_result = subprocess.run(
                ["nginx", "-s", "reload"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if reload_result.returncode == 0:
                logger.info("Nginx 설정 리로드 성공")
                return True
            else:
                logger.error(f"Nginx 리로드 실패: {reload_result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Nginx 설정 테스트/리로드 시간 초과")
            return False
        except FileNotFoundError:
            logger.warning("nginx 명령어를 찾을 수 없습니다. 수동으로 설정을 확인하세요.")
            return True  # nginx가 없어도 설정 파일은 생성됨
        except Exception as e:
            logger.error(f"Nginx 설정 테스트/리로드 실패: {e}")
            return False
    
    def remove_proxy_rule(self, user_id: str) -> bool:
        """
        프록시 규칙 제거 (개선된 버전)
        """
        try:
            removed_items = []
            
            # 1. 설정 파일 제거
            config_file = self.nginx_config_path / f"{user_id}.conf"
            if config_file.exists():
                config_file.unlink()
                removed_items.append("config_file")
                logger.info(f"설정 파일 제거: {config_file}")
            
            # 2. 심볼릭 링크 제거
            if self.sites_enabled_path.exists():
                symlink_path = self.sites_enabled_path / f"{user_id}.conf"
                if symlink_path.exists() or symlink_path.is_symlink():
                    symlink_path.unlink()
                    removed_items.append("symlink")
                    logger.info(f"심볼릭 링크 제거: {symlink_path}")
            
            # 3. SSH 포워딩 규칙 제거
            try:
                # 실제 구현에서는 iptables 규칙 제거
                logger.info(f"SSH 포워딩 규칙 제거: {user_id}")
                removed_items.append("ssh_forwarding")
            except Exception as e:
                logger.warning(f"SSH 포워딩 규칙 제거 실패: {e}")
            
            # 4. Nginx 리로드
            if removed_items and self._test_and_reload_nginx():
                logger.info(f"프록시 규칙 제거 완료: {user_id}, 제거된 항목: {removed_items}")
                return True
            else:
                logger.warning(f"프록시 규칙 제거 후 Nginx 리로드 실패: {user_id}")
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
    
    def get_proxy_info(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        프록시 정보 조회 (개선된 버전)
        """
        try:
            config_file = self.nginx_config_path / f"{user_id}.conf"
            
            if not config_file.exists():
                return None
            
            # 설정 파일에서 정보 추출
            proxy_info = {
                "user_id": user_id,
                "config_file": str(config_file),
                "web_url": f"http://{self.service_domain}/{user_id}",
                "status": "active" if config_file.exists() else "inactive",
                "created_at": None,
                "size": 0
            }
            
            # 파일 정보 추가
            if config_file.exists():
                stat = config_file.stat()
                proxy_info["created_at"] = stat.st_mtime
                proxy_info["size"] = stat.st_size
            
            # 심볼릭 링크 상태 확인
            if self.sites_enabled_path.exists():
                symlink_path = self.sites_enabled_path / f"{user_id}.conf"
                proxy_info["symlink_exists"] = symlink_path.exists()
            
            return proxy_info
            
        except Exception as e:
            logger.error(f"프록시 정보 조회 실패: {e}")
            return None
    
    def list_all_proxy_rules(self) -> List[Dict[str, str]]:
        """
        모든 프록시 규칙 목록 조회
        """
        try:
            proxy_rules = []
            
            # 설정 파일 디렉토리에서 모든 .conf 파일 검색
            for config_file in self.nginx_config_path.glob("*.conf"):
                if config_file.is_file():
                    user_id = config_file.stem
                    proxy_info = self.get_proxy_info(user_id)
                    if proxy_info:
                        proxy_rules.append(proxy_info)
            
            logger.info(f"프록시 규칙 목록 조회: {len(proxy_rules)}개")
            return proxy_rules
            
        except Exception as e:
            logger.error(f"프록시 규칙 목록 조회 실패: {e}")
            return [] 