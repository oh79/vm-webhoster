"""
Nginx 프록시 서비스 - 웹/SSH 포트 포워딩 관리 (개선된 자동화 버전)
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
    """Nginx 프록시 관리 서비스 (자동화 개선 버전)"""
    
    def __init__(self):
        self.nginx_config_path = Path(settings.NGINX_CONFIG_PATH)
        self.sites_enabled_path = Path("/etc/nginx/sites-enabled")
        self.service_domain = settings.SERVICE_DOMAIN
        self.project_root = Path(__file__).parent.parent.parent.parent
        
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
        
        # nginx 스크립트 권한 설정
        self._setup_scripts()
    
    def _ensure_directories(self):
        """필요한 디렉토리들이 존재하는지 확인하고 생성"""
        try:
            # Nginx 설정 디렉토리 생성
            self.nginx_config_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Nginx 설정 디렉토리 확인: {self.nginx_config_path}")
            
            # 백업 디렉토리 생성
            backup_dir = self.nginx_config_path / "backup"
            backup_dir.mkdir(exist_ok=True)
            
            # 스크립트 디렉토리 생성
            scripts_dir = self.project_root / "scripts"
            scripts_dir.mkdir(exist_ok=True)
                
        except Exception as e:
            logger.error(f"디렉토리 생성 실패: {e}")
            raise VMOperationError(f"프록시 디렉토리 설정 실패: {e}")
    
    def _setup_scripts(self):
        """nginx 적용 스크립트 권한 설정"""
        try:
            scripts_dir = self.project_root / "scripts"
            apply_script = scripts_dir / "apply_nginx_config.sh"
            remove_script = scripts_dir / "remove_nginx_config.sh"
            
            # 스크립트에 실행 권한 부여
            if apply_script.exists():
                apply_script.chmod(0o755)
                logger.info(f"apply_nginx_config.sh 권한 설정 완료")
            
            if remove_script.exists():
                remove_script.chmod(0o755)
                logger.info(f"remove_nginx_config.sh 권한 설정 완료")
                
        except Exception as e:
            logger.warning(f"스크립트 권한 설정 실패: {e}")
    
    def add_proxy_rule(self, user_id: str, vm_ip: str, ssh_port: int, web_port: int = None) -> Dict[str, str]:
        """
        사용자별 프록시 규칙 추가 (자동화 개선 버전)
        /<user_id> -> VM의 웹포트로 프록시
        """
        try:
            # 웹 포트가 제공되지 않으면 SSH 포트 기반으로 추정
            if not web_port:
                web_port = 8000 + (hash(user_id) % 1000)
            
            # Nginx 설정 파일 생성 (location 블록만 생성하여 충돌 방지)
            config_content = f"""# 사용자 {user_id}의 웹 호스팅 프록시 설정
# 생성 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}
# 이 파일은 webhosting.conf에 include되어 사용됩니다

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
    
    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}}

# SSH 포트 포워딩 정보
# SSH 접속: ssh -p {ssh_port} user@localhost
"""
            
            # 설정 파일 저장
            config_file = self.nginx_config_path / f"{user_id}.conf"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
                
            logger.info(f"프록시 설정 파일 생성: {config_file}")
            
            # 스크립트를 통한 자동 적용 시도
            applied = self._apply_nginx_config_with_script(user_id, config_file)
            
            # 결과 정보 생성
            result = {
                'web_url': f"http://{self.service_domain.split(':')[0]}/{user_id}",
                'ssh_command': f"ssh -p {ssh_port} ubuntu@{self.service_domain.split(':')[0]}",
                'ssh_port': str(ssh_port),
                'vm_ip': vm_ip,
                'web_port': str(web_port),
                'nginx_applied': applied,
                'config_file': str(config_file)
            }
            
            if applied:
                logger.info(f"✅ 프록시 설정 자동 적용 완료: {result['web_url']}")
            else:
                logger.warning(f"⚠️ 프록시 설정 파일만 생성됨 (수동 적용 필요): {config_file}")
                result['manual_command'] = f"sudo bash scripts/apply_nginx_config.sh {user_id} {config_file}"
            
            return result
            
        except Exception as e:
            logger.error(f"프록시 설정 생성 실패: {e}")
            raise VMOperationError(f"프록시 설정 생성 실패: {e}")
    
    def _apply_nginx_config_with_script(self, user_id: str, config_file: Path) -> bool:
        """
        스크립트를 통한 nginx 설정 자동 적용 (webhosting.conf 직접 수정 방식)
        """
        try:
            # 1. 기존 스크립트 방식도 시도 (개별 설정 파일)
            script_path = self.project_root / "scripts" / "apply_nginx_config.sh"
            if script_path.exists():
                try:
                    cmd = ["bash", str(script_path), user_id, str(config_file)]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        logger.info(f"개별 설정 파일 방식 성공: {user_id}")
                        return True
                except Exception:
                    pass
            
            # 2. webhosting.conf 직접 수정 방식
            return self._update_webhosting_config(user_id, config_file)
                
        except Exception as e:
            logger.error(f"nginx 설정 적용 오류: {e}")
            return False
    
    def _update_webhosting_config(self, user_id: str, config_file: Path) -> bool:
        """
        webhosting.conf 파일을 직접 수정하여 사용자 설정 추가
        """
        try:
            # 설정 파일에서 웹 포트 추출
            with open(config_file, 'r') as f:
                content = f.read()
                
            # proxy_pass에서 포트 번호 추출
            import re
            port_match = re.search(r'proxy_pass http://127\.0\.0\.1:(\d+);', content)
            if not port_match:
                logger.error(f"웹 포트를 찾을 수 없습니다: {config_file}")
                return False
                
            web_port = port_match.group(1)
            
            # update_webhosting_config.sh 스크립트 실행
            update_script = self.project_root / "scripts" / "update_webhosting_config.sh"
            if not update_script.exists():
                logger.warning(f"webhosting 업데이트 스크립트를 찾을 수 없습니다: {update_script}")
                return self._manual_webhosting_update(user_id, web_port)
            
            cmd = ["bash", str(update_script), user_id, web_port]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                logger.info(f"webhosting.conf 자동 업데이트 성공: {user_id}")
                return True
            else:
                logger.warning(f"webhosting.conf 업데이트 실패: {result.stderr}")
                return self._manual_webhosting_update(user_id, web_port)
                
        except Exception as e:
            logger.error(f"webhosting.conf 업데이트 오류: {e}")
            return False
    
    def _manual_webhosting_update(self, user_id: str, web_port: str) -> bool:
        """
        webhosting.conf 수동 업데이트 (스크립트 실패 시 대안)
        """
        try:
            webhosting_config = "/etc/nginx/sites-available/webhosting"
            
            # 이미 해당 사용자 설정이 있는지 확인
            check_cmd = f"sudo grep -q 'location /{user_id}' {webhosting_config}"
            result = subprocess.run(check_cmd, shell=True, capture_output=True)
            
            if result.returncode == 0:
                logger.info(f"사용자 {user_id} 설정이 이미 존재합니다.")
                return True
            
            # 임시 파일로 location 블록 생성
            location_content = f"""    # 사용자 {user_id}번 VM 호스팅 (포트 {web_port})
    location /{user_id} {{
        rewrite ^/{user_id}(/.*)$ $1 break;
        rewrite ^/{user_id}$ / break;
        
        proxy_pass http://127.0.0.1:{web_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}"""
            
            temp_file = f"/tmp/user{user_id}_location.txt"
            with open(temp_file, 'w') as f:
                f.write(location_content)
            
            # webhosting.conf 업데이트
            update_cmd = f"""sudo sh -c 'head -n -1 {webhosting_config} > /tmp/webhosting_new && 
                            cat {temp_file} >> /tmp/webhosting_new && 
                            echo "}})" >> /tmp/webhosting_new && 
                            mv /tmp/webhosting_new {webhosting_config}'"""
            
            result = subprocess.run(update_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # nginx 테스트 및 리로드
                test_result = subprocess.run(["sudo", "nginx", "-t"], capture_output=True)
                if test_result.returncode == 0:
                    reload_result = subprocess.run(["sudo", "systemctl", "reload", "nginx"], capture_output=True)
                    if reload_result.returncode == 0:
                        logger.info(f"webhosting.conf 수동 업데이트 성공: {user_id}")
                        return True
            
            logger.error(f"webhosting.conf 수동 업데이트 실패: {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"수동 업데이트 오류: {e}")
            return False
    
    def remove_proxy_rule(self, user_id: str) -> bool:
        """
        사용자별 프록시 규칙 제거 (자동화 개선 버전)
        """
        try:
            # 로컬 설정 파일 제거
            config_file = self.nginx_config_path / f"{user_id}.conf"
            if config_file.exists():
                # 백업 생성
                backup_dir = self.nginx_config_path / "backup"
                backup_file = backup_dir / f"{user_id}.conf.{int(time.time())}"
                config_file.rename(backup_file)
                logger.info(f"설정 파일 백업: {backup_file}")
            
            # 스크립트를 통한 시스템 설정 제거
            removed = self._remove_nginx_config_with_script(user_id)
            
            if removed:
                logger.info(f"✅ 프록시 설정 자동 제거 완료: {user_id}")
            else:
                logger.warning(f"⚠️ 프록시 설정 부분 제거됨 (수동 정리 필요): {user_id}")
            
            return removed
            
        except Exception as e:
            logger.error(f"프록시 설정 제거 실패: {e}")
            return False
    
    def _remove_nginx_config_with_script(self, user_id: str) -> bool:
        """
        스크립트를 통한 nginx 설정 제거
        """
        try:
            script_path = self.project_root / "scripts" / "remove_nginx_config.sh"
            
            if not script_path.exists():
                logger.warning(f"nginx 제거 스크립트를 찾을 수 없습니다: {script_path}")
                return False
            
            # 스크립트 실행
            cmd = ["bash", str(script_path), user_id]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                logger.info(f"nginx 설정 자동 제거 성공: {user_id}")
                logger.debug(f"스크립트 출력: {result.stdout}")
                return True
            else:
                logger.warning(f"nginx 설정 제거 스크립트 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"nginx 설정 제거 스크립트 타임아웃: {user_id}")
            return False
        except Exception as e:
            logger.error(f"nginx 설정 제거 스크립트 오류: {e}")
            return False
    
    def list_active_proxies(self) -> List[Dict[str, str]]:
        """
        활성화된 프록시 목록 조회
        """
        try:
            proxies = []
            
            # sites-enabled 디렉토리 스캔
            if self.sites_enabled_path.exists():
                for config_file in self.sites_enabled_path.glob("*.conf"):
                    if config_file.is_symlink() and config_file.name != "default":
                        user_id = config_file.stem
                        proxies.append({
                            'user_id': user_id,
                            'config_file': str(config_file),
                            'web_url': f"http://{self.service_domain.split(':')[0]}/{user_id}",
                            'status': 'active'
                        })
            
            logger.info(f"활성 프록시 조회: {len(proxies)}개")
            return proxies
            
        except Exception as e:
            logger.error(f"프록시 목록 조회 실패: {e}")
            return []
    
    def get_proxy_status(self, user_id: str) -> Dict[str, any]:
        """
        특정 사용자의 프록시 상태 조회
        """
        try:
            config_file = self.nginx_config_path / f"{user_id}.conf"
            sites_enabled_file = self.sites_enabled_path / f"{user_id}.conf"
            
            status = {
                'user_id': user_id,
                'config_exists': config_file.exists(),
                'nginx_enabled': sites_enabled_file.exists(),
                'web_url': f"http://{self.service_domain.split(':')[0]}/{user_id}",
                'local_config_path': str(config_file),
                'nginx_config_path': str(sites_enabled_file)
            }
            
            # nginx 설정 테스트
            if sites_enabled_file.exists():
                try:
                    result = subprocess.run(
                        ["sudo", "nginx", "-t"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    status['nginx_test_ok'] = result.returncode == 0
                    if result.returncode != 0:
                        status['nginx_error'] = result.stderr
                except Exception:
                    status['nginx_test_ok'] = False
            
            return status
            
        except Exception as e:
            logger.error(f"프록시 상태 조회 실패: {e}")
            return {'user_id': user_id, 'error': str(e)} 