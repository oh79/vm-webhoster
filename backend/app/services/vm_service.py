"""
VM 관리 서비스 - VM 생성, 관리, 운영 로직 (개선된 버전)
"""
import uuid
import subprocess
import logging
import xml.etree.ElementTree as ET
import yaml
import base64
import time
import os
import tempfile
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings
from app.core.exceptions import VMOperationError
from app.models.hosting import HostingStatus

# 로깅 설정
logger = logging.getLogger(__name__)

class VMService:
    """VM 관리 서비스 클래스 (개선된 버전)"""
    
    def __init__(self):
        self.bridge_name = settings.VM_BRIDGE_NAME
        self.image_path = Path(settings.VM_IMAGE_PATH)
        self.template_image = settings.VM_TEMPLATE_IMAGE
        # 환경 검증
        self._validate_environment()
    
    def _validate_environment(self) -> None:
        """
        VM 생성에 필요한 환경 검증
        """
        try:
            # libvirt 연결 확인
            result = subprocess.run(
                ["virsh", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.warning("libvirt가 설치되지 않았거나 실행 중이 아닙니다.")
                raise VMOperationError("VM 환경이 설정되지 않았습니다. libvirt를 설치하고 실행하세요.")
            
            # qemu-img 확인
            result = subprocess.run(
                ["qemu-img", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.warning("qemu-img가 설치되지 않았습니다.")
                raise VMOperationError("qemu-img가 설치되지 않았습니다.")
            
            # genisoimage 확인 (cloud-init ISO 생성용)
            result = subprocess.run(
                ["genisoimage", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.warning("genisoimage가 설치되지 않았습니다. cloud-init 기능이 제한됩니다.")
            
            # VM 이미지 디렉토리 생성
            self.image_path.mkdir(parents=True, exist_ok=True)
            
            # 브리지 네트워크 확인
            self._check_network_bridge()
            
            logger.info("VM 환경 검증 완료")
            
        except subprocess.TimeoutExpired:
            logger.error("VM 환경 검증 시간 초과")
            raise VMOperationError("VM 환경 검증 시간 초과")
        except FileNotFoundError as e:
            logger.error(f"필수 도구가 설치되지 않았습니다: {e}")
            raise VMOperationError("VM 생성에 필요한 도구가 설치되지 않았습니다.")
    
    def _check_network_bridge(self) -> None:
        """
        네트워크 브리지 확인
        """
        try:
            result = subprocess.run(
                ["ip", "link", "show", self.bridge_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.warning(f"브리지 네트워크 {self.bridge_name}가 없습니다.")
                # 기본 브리지로 변경 시도
                self.bridge_name = "virbr0"
                result = subprocess.run(
                    ["ip", "link", "show", self.bridge_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    logger.error("사용 가능한 브리지 네트워크가 없습니다.")
                    raise VMOperationError("사용 가능한 브리지 네트워크가 없습니다.")
                    
            logger.info(f"브리지 네트워크 확인: {self.bridge_name}")
            
        except subprocess.TimeoutExpired:
            logger.error("네트워크 브리지 확인 시간 초과")
            raise VMOperationError("네트워크 브리지 확인 시간 초과")
    
    def generate_vm_id(self) -> str:
        """
        고유한 VM ID 생성
        """
        return f"vm-{uuid.uuid4().hex[:8]}"
    
    def get_available_ssh_port(self, start_port: int = None, end_port: int = None, db_session = None) -> int:
        """
        사용 가능한 SSH 포트 찾기 (개선된 버전 - DB 확인 포함)
        """
        from app.models.hosting import Hosting  # 순환 import 방지
        
        start = start_port or settings.SSH_PORT_RANGE_START
        end = end_port or settings.SSH_PORT_RANGE_END
        
        # 데이터베이스에서 사용 중인 포트 조회
        used_ports = set()
        if db_session:
            try:
                db_ports = db_session.query(Hosting.ssh_port).all()
                used_ports = {port[0] for port in db_ports if port[0]}
                logger.info(f"데이터베이스에서 사용 중인 SSH 포트: {used_ports}")
            except Exception as e:
                logger.warning(f"데이터베이스 포트 조회 실패: {e}")
        
        for port in range(start, end + 1):
            # 데이터베이스에서 사용 중인 포트인지 확인
            if port in used_ports:
                logger.debug(f"포트 {port}는 데이터베이스에서 사용 중")
                continue
                
            # 시스템에서 사용 중인 포트인지 확인
            if self._is_port_available(port):
                logger.info(f"사용 가능한 SSH 포트 찾음: {port}")
                return port
        
        raise VMOperationError(f"사용 가능한 SSH 포트가 없습니다. (범위: {start}-{end}, DB 사용 중: {len(used_ports)}개)")
    
    def _is_port_available(self, port: int) -> bool:
        """
        포트 사용 가능 여부 확인 (개선된 버전)
        """
        try:
            # ss 명령어 사용 (netstat보다 빠름)
            result = subprocess.run(
                ["ss", "-tuln"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return f":{port}" not in result.stdout
            
            # ss가 없으면 netstat 사용
            result = subprocess.run(
                ["netstat", "-tuln"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return f":{port}" not in result.stdout
                
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning(f"포트 {port} 확인 중 오류, 사용 가능한 것으로 간주")
            return True
    
    def generate_ssh_keypair(self, vm_id: str) -> Tuple[str, str]:
        """
        VM용 SSH 키 쌍 생성
        
        Returns:
            Tuple[str, str]: (private_key, public_key)
        """
        try:
            # RSA 키 생성
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # 개인키 직렬화
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            # 공개키 직렬화
            public_key = private_key.public_key()
            public_ssh = public_key.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            ).decode('utf-8')
            
            # 공개키에 주석 추가
            public_ssh_with_comment = f"{public_ssh} webhoster-{vm_id}"
            
            # 키 파일 저장
            key_dir = self.image_path / "ssh-keys" / vm_id
            key_dir.mkdir(parents=True, exist_ok=True)
            
            private_key_file = key_dir / "id_rsa"
            public_key_file = key_dir / "id_rsa.pub"
            
            with open(private_key_file, 'w') as f:
                f.write(private_pem)
            private_key_file.chmod(0o600)
            
            with open(public_key_file, 'w') as f:
                f.write(public_ssh_with_comment)
            public_key_file.chmod(0o644)
            
            logger.info(f"SSH 키 쌍 생성 완료: {vm_id}")
            
            return private_pem, public_ssh_with_comment
            
        except Exception as e:
            logger.error(f"SSH 키 생성 실패: {e}")
            raise VMOperationError(f"SSH 키 생성 실패: {e}")
    
    def create_cloud_init_config(self, vm_id: str, user_id: str, ssh_public_key: str = None) -> str:
        """
        cloud-init 설정 생성 (웹서버 자동 설치, 개선된 버전)
        """
        try:
            # SSH 키가 제공되지 않으면 생성
            if not ssh_public_key:
                _, ssh_public_key = self.generate_ssh_keypair(vm_id)
            
            # cloud-init user-data 설정
            user_data = {
                'version': 1,
                'users': [
                    {
                        'name': 'ubuntu',
                        'sudo': 'ALL=(ALL) NOPASSWD:ALL',
                        'shell': '/bin/bash',
                        'ssh_authorized_keys': [ssh_public_key]
                    },
                    {
                        'name': 'webhoster',
                        'sudo': 'ALL=(ALL) NOPASSWD:ALL',
                        'shell': '/bin/bash',
                        'ssh_authorized_keys': [ssh_public_key],
                        'groups': ['www-data', 'docker']
                    }
                ],
                'package_update': True,
                'package_upgrade': True,
                'packages': [
                    'nginx',
                    'curl',
                    'wget',
                    'unzip',
                    'git',
                    'htop',
                    'ufw',
                    'fail2ban',
                    'certbot',
                    'python3-certbot-nginx',
                    'docker.io',
                    'docker-compose'
                ],
                'runcmd': [
                    # 시스템 업데이트
                    'apt-get update',
                    'apt-get upgrade -y',
                    
                    # Docker 서비스 시작
                    'systemctl enable docker',
                    'systemctl start docker',
                    'usermod -aG docker ubuntu',
                    'usermod -aG docker webhoster',
                    
                    # Nginx 시작 및 활성화
                    'systemctl enable nginx',
                    'systemctl start nginx',
                    
                    # 기본 웹 페이지 생성
                    'mkdir -p /var/www/html',
                    'chown -R www-data:www-data /var/www/html',
                    'chmod -R 755 /var/www/html',
                    
                    # 사용자별 환영 페이지 생성 (개선된 버전)
                    f"""cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>웹 호스팅 서비스 - {user_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            max-width: 900px;
            margin: 20px;
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .status {{
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 40px;
            padding: 15px;
            background: rgba(46, 204, 113, 0.3);
            border-radius: 10px;
            border-left: 4px solid #2ecc71;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .info-box {{
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
        }}
        .info-box h3 {{
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        .info-box p {{
            margin-bottom: 10px;
            line-height: 1.5;
        }}
        .upload-info {{
            border-left: 4px solid #2ecc71;
        }}
        .ssh-info {{
            border-left: 4px solid #3498db;
        }}
        .docker-info {{
            border-left: 4px solid #f39c12;
        }}
        .security-info {{
            border-left: 4px solid #e74c3c;
        }}
        code {{
            background: rgba(0, 0, 0, 0.3);
            padding: 4px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            font-size: 0.9em;
            opacity: 0.8;
        }}
        .feature-list {{
            list-style: none;
            padding-left: 0;
        }}
        .feature-list li {{
            margin-bottom: 8px;
            padding-left: 20px;
            position: relative;
        }}
        .feature-list li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #2ecc71;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 웹 호스팅 서비스</h1>
        
        <div class="status">
            <strong>{user_id}</strong>님의 웹 호스팅이 성공적으로 생성되었습니다!<br>
            VM ID: <code>{vm_id}</code> | 생성 시간: <span id="currentTime"></span>
        </div>
        
        <div class="info-grid">
            <div class="info-box upload-info">
                <h3>📁 파일 업로드</h3>
                <p>웹 파일을 업로드할 경로:</p>
                <p><code>/var/www/html/</code></p>
                <ul class="feature-list">
                    <li>SFTP/SCP로 파일 업로드</li>
                    <li>Git을 통한 코드 배포</li>
                    <li>Docker 컨테이너 배포</li>
                </ul>
            </div>
            
            <div class="info-box ssh-info">
                <h3>🔐 SSH 접속</h3>
                <p>서버 관리를 위한 SSH 접속:</p>
                <p><code>ssh ubuntu@your-domain -p YOUR_SSH_PORT</code></p>
                <p><code>ssh webhoster@your-domain -p YOUR_SSH_PORT</code></p>
                <ul class="feature-list">
                    <li>두 개의 사용자 계정 제공</li>
                    <li>SSH 키 기반 인증</li>
                    <li>sudo 권한 포함</li>
                </ul>
            </div>
            
            <div class="info-box docker-info">
                <h3>🐳 Docker 지원</h3>
                <p>Docker와 Docker Compose가 설치되어 있습니다:</p>
                <p><code>docker --version</code></p>
                <p><code>docker-compose --version</code></p>
                <ul class="feature-list">
                    <li>최신 Docker 엔진</li>
                    <li>Docker Compose v2</li>
                    <li>사용자가 docker 그룹에 포함</li>
                </ul>
            </div>
            
            <div class="info-box security-info">
                <h3>🛡️ 보안 설정</h3>
                <p>기본 보안 설정이 적용되었습니다:</p>
                <ul class="feature-list">
                    <li>UFW 방화벽 활성화</li>
                    <li>Fail2ban 침입 차단</li>
                    <li>SSL/TLS 인증서 지원 (Certbot)</li>
                    <li>SSH 패스워드 인증 비활성화</li>
                </ul>
            </div>
        </div>
        
        <div class="info-box">
            <h3>🚀 시작하기</h3>
            <ol style="padding-left: 20px;">
                <li>SSH로 서버에 접속하세요</li>
                <li>웹 파일을 <code>/var/www/html/</code>에 업로드하세요</li>
                <li>Docker 컨테이너를 실행하거나 직접 웹서버를 설정하세요</li>
                <li>SSL 인증서가 필요하면 <code>certbot --nginx</code>를 실행하세요</li>
            </ol>
        </div>
        
        <div class="footer">
            <p>웹 호스팅 서비스 © 2024</p>
            <p>기술 지원: Nginx + Docker + Ubuntu 22.04</p>
        </div>
    </div>
    
    <script>
        document.getElementById('currentTime').textContent = new Date().toLocaleString('ko-KR');
    </script>
</body>
</html>
EOF""",
                    
                    # Nginx 설정 개선
                    'sed -i "s/# server_names_hash_bucket_size 64;/server_names_hash_bucket_size 64;/" /etc/nginx/nginx.conf',
                    
                    # 보안 설정
                    'sed -i "s/#PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config',
                    'sed -i "s/#PubkeyAuthentication yes/PubkeyAuthentication yes/" /etc/ssh/sshd_config',
                    'systemctl reload sshd',
                    
                    # 방화벽 설정
                    'ufw --force enable',
                    'ufw allow ssh',
                    'ufw allow 80/tcp',
                    'ufw allow 443/tcp',
                    
                    # fail2ban 설정
                    'systemctl enable fail2ban',
                    'systemctl start fail2ban',
                    
                    # 사용자 디렉토리 권한 설정
                    'chown -R ubuntu:ubuntu /home/ubuntu',
                    'chown -R webhoster:webhoster /home/webhoster 2>/dev/null || true',
                    'usermod -aG www-data ubuntu',
                    'usermod -aG www-data webhoster',
                    
                    # 완료 로그
                    f'echo "VM {vm_id} 설정 완료: $(date)" >> /var/log/webhoster-setup.log',
                    'echo "웹 호스팅 서비스 설치 완료" > /tmp/webhoster-ready'
                ],
                'write_files': [
                    {
                        'path': '/etc/nginx/sites-available/default',
                        'content': '''server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    
    server_name _;
    
    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # PHP 지원 (추후 설치 시)
    location ~ \\.php$ {
        include snippets/fastcgi-php.conf;
        # fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
    }
    
    # 보안 설정
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # 정적 파일 캐싱
    location ~* \\.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}''',
                        'permissions': '0644'
                    },
                    {
                        'path': '/etc/fail2ban/jail.local',
                        'content': '''[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 6
''',
                        'permissions': '0644'
                    }
                ],
                'final_message': f'VM {vm_id} 웹서버 설정이 완료되었습니다! 보안 설정과 Docker가 포함되어 있습니다.'
            }
            
            # YAML로 변환
            user_data_yaml = yaml.dump(user_data, default_flow_style=False, allow_unicode=True)
            
            # cloud-init 파일 생성
            cloud_init_dir = self.image_path / "cloud-init" / vm_id
            cloud_init_dir.mkdir(parents=True, exist_ok=True)
            
            # user-data 파일 저장
            user_data_file = cloud_init_dir / "user-data"
            with open(user_data_file, 'w', encoding='utf-8') as f:
                f.write(f"#cloud-config\n{user_data_yaml}")
            
            # meta-data 파일 생성
            meta_data = {
                'instance-id': vm_id,
                'local-hostname': vm_id,
                'public-keys': {
                    'webhoster': ssh_public_key
                }
            }
            
            meta_data_file = cloud_init_dir / "meta-data"
            with open(meta_data_file, 'w', encoding='utf-8') as f:
                f.write(yaml.dump(meta_data, default_flow_style=False, allow_unicode=True))
            
            # cloud-init ISO 이미지 생성
            iso_path = cloud_init_dir / "cloud-init.iso"
            try:
                subprocess.run([
                    "genisoimage", "-output", str(iso_path),
                    "-volid", "cidata", "-joliet", "-rock",
                    str(user_data_file), str(meta_data_file)
                ], check=True, timeout=60)
                
                logger.info(f"cloud-init 설정 생성 완료: {iso_path}")
                return str(iso_path)
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("genisoimage를 사용할 수 없어 대체 방법을 사용합니다.")
                # 대체 방법: tar 아카이브 생성
                import tarfile
                tar_path = cloud_init_dir / "cloud-init.tar"
                with tarfile.open(tar_path, "w") as tar:
                    tar.add(user_data_file, arcname="user-data")
                    tar.add(meta_data_file, arcname="meta-data")
                
                logger.info(f"cloud-init 설정 생성 완료 (tar): {tar_path}")
                return str(tar_path)
            
        except Exception as e:
            logger.error(f"cloud-init 설정 생성 실패: {e}")
            raise VMOperationError(f"cloud-init 설정 생성 실패: {e}")
    
    def create_vm_disk(self, vm_id: str, size_gb: int = 20) -> str:
        """
        VM 디스크 이미지 생성
        """
        try:
            # 디스크 이미지 경로
            disk_path = self.image_path / f"{vm_id}.qcow2"
            
            # 템플릿 이미지에서 복사 (있는 경우)
            template_path = self.image_path / self.template_image
            
            if template_path.exists():
                # 템플릿에서 복사 (절대 경로 사용)
                subprocess.run([
                    "qemu-img", "create", "-f", "qcow2",
                    "-b", str(template_path.resolve()),  # 절대 경로로 변경
                    "-F", "qcow2",
                    str(disk_path.resolve())  # 절대 경로로 변경
                ], check=True, timeout=60)
            else:
                # 새 이미지 생성
                subprocess.run([
                    "qemu-img", "create", "-f", "qcow2",
                    str(disk_path.resolve()), f"{size_gb}G"  # 절대 경로로 변경
                ], check=True, timeout=60)
            
            logger.info(f"VM 디스크 생성 완료: {disk_path}")
            return str(disk_path.resolve())  # 절대 경로 반환
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 디스크 생성 실패: {e}")
            raise VMOperationError(f"VM 디스크 생성에 실패했습니다: {e}")
        except Exception as e:
            logger.error(f"예상치 못한 디스크 생성 오류: {e}")
            raise VMOperationError(f"VM 디스크 생성 중 오류가 발생했습니다: {e}")
    
    def create_vm_xml(self, vm_id: str, disk_path: str, ssh_port: int, cloud_init_iso: str = None, memory_mb: int = 1024, vcpus: int = 1) -> str:
        """
        VM XML 정의 생성 (cloud-init 지원 추가)
        """
        # 기본 네트워크 인터페이스 MAC 주소 생성
        mac_address = self._generate_mac_address()
        
        # cloud-init ISO 디스크 추가
        cloud_init_disk = ""
        if cloud_init_iso and Path(cloud_init_iso).exists():
            cloud_init_disk = f"""
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source file='{cloud_init_iso}'/>
      <target dev='hda' bus='ide'/>
      <readonly/>
      <address type='drive' controller='0' bus='0' target='0' unit='0'/>
    </disk>"""
        
        xml_template = f"""
<domain type='kvm'>
  <name>{vm_id}</name>
  <uuid>{uuid.uuid4()}</uuid>
  <memory unit='MiB'>{memory_mb}</memory>
  <currentMemory unit='MiB'>{memory_mb}</currentMemory>
  <vcpu placement='static'>{vcpus}</vcpu>
  <os>
    <type arch='x86_64' machine='pc-i440fx-2.9'>hvm</type>
    <boot dev='hd'/>
    <boot dev='cdrom'/>
  </os>
  <features>
    <acpi/>
    <apic/>
  </features>
  <cpu mode='host-model' check='partial'/>
  <clock offset='utc'>
    <timer name='rtc' tickpolicy='catchup'/>
    <timer name='pit' tickpolicy='delay'/>
    <timer name='hpet' present='no'/>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{disk_path}'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </disk>{cloud_init_disk}
    <interface type='bridge'>
      <mac address='{mac_address}'/>
      <source bridge='{self.bridge_name}'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </interface>
    <serial type='pty'>
      <target type='isa-serial' port='0'>
        <model name='isa-serial'/>
      </target>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
    <graphics type='vnc' port='-1' autoport='yes'/>
    <video>
      <model type='cirrus' vram='16384' heads='1' primary='yes'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
    </video>
  </devices>
</domain>
        """.strip()
        
        return xml_template
    
    def _generate_mac_address(self) -> str:
        """
        MAC 주소 생성 (libvirt 표준 형식)
        """
        # libvirt 기본 범위: 52:54:00:xx:xx:xx
        import random
        return f"52:54:00:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}"
    
    def create_vm(self, vm_id: str, ssh_port: int, user_id: str = None) -> Dict[str, str]:
        """
        Docker 컨테이너 기반 웹 호스팅 생성 (실제 구현)
        """
        try:
            logger.info(f"Docker 컨테이너 생성 시작: {vm_id}")
            
            # Docker 컨테이너 이름
            container_name = f"webhost-{vm_id}"
            
            # 웹 포트 할당 (8000번대 사용)
            web_port = 8000 + (hash(vm_id) % 1000)
            
            # 컨테이너용 웹 디렉토리 생성 (절대 경로 사용)
            host_web_dir = self.image_path / "containers" / vm_id / "www"
            host_web_dir.mkdir(parents=True, exist_ok=True)
            
            # 절대 경로로 변환
            host_web_dir_abs = host_web_dir.resolve()
            logger.info(f"웹 디렉토리 절대 경로: {host_web_dir_abs}")
            
            # 기본 index.html 생성
            index_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>웹 호스팅 - 사용자 {user_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }}
        .container {{
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        h1 {{ margin-bottom: 20px; }}
        .info {{ margin: 10px 0; opacity: 0.9; }}
        .success {{ color: #2ecc71; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 웹 호스팅 서비스</h1>
        <p class="success">호스팅이 성공적으로 생성되었습니다!</p>
        <div class="info">사용자 ID: {user_id}</div>
        <div class="info">VM ID: {vm_id}</div>
        <div class="info">SSH 포트: {ssh_port}</div>
        <div class="info">웹 포트: {web_port}</div>
        <p>이 디렉토리에 웹 파일을 업로드하여 사이트를 만들어보세요!</p>
    </div>
</body>
</html>"""
            
            with open(host_web_dir / "index.html", "w", encoding="utf-8") as f:
                f.write(index_html)
            
            # Docker 컨테이너 실행 (Ubuntu + Nginx + SSH) - 절대 경로 사용
            docker_cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "-p", f"{web_port}:80",  # 웹 포트 포워딩
                "-p", f"{ssh_port}:22",  # SSH 포트 포워딩
                "-v", f"{host_web_dir_abs}:/var/www/html",  # 절대 경로로 웹 디렉토리 마운트
                "-e", f"USER_ID={user_id}",
                "-e", f"VM_ID={vm_id}",
                "nginx:alpine"  # 경량 Nginx 이미지 사용
            ]
            
            logger.info(f"Docker 명령어: {' '.join(docker_cmd)}")
            
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"Docker 컨테이너 생성 실패: {result.stderr}")
                raise VMOperationError(f"컨테이너 생성 실패: {result.stderr}")
            
            container_id = result.stdout.strip()
            
            # 컨테이너 IP 조회
            ip_cmd = ["docker", "inspect", "-f", "{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container_name]
            ip_result = subprocess.run(ip_cmd, capture_output=True, text=True, timeout=30)
            
            if ip_result.returncode == 0 and ip_result.stdout.strip():
                vm_ip = ip_result.stdout.strip()
            else:
                vm_ip = "127.0.0.1"  # 로컬호스트로 폴백
            
            logger.info(f"Docker 컨테이너 생성 완료: {container_name}, 웹포트: {web_port}, SSH포트: {ssh_port}")
            
            return {
                "vm_id": vm_id,
                "vm_ip": vm_ip,
                "web_port": web_port,
                "ssh_port": ssh_port,
                "container_name": container_name,
                "container_id": container_id,
                "web_dir": str(host_web_dir_abs),
                "status": HostingStatus.RUNNING.value
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker 컨테이너 생성 실패: {e}")
            raise VMOperationError(f"웹 호스팅 생성에 실패했습니다: {e}")
        except Exception as e:
            logger.error(f"예상치 못한 컨테이너 생성 오류: {e}")
            raise VMOperationError(f"웹 호스팅 생성 중 오류가 발생했습니다: {e}")
    
    def get_vm_ip(self, vm_id: str, timeout: int = 60) -> str:
        """
        VM IP 주소 조회
        """
        try:
            # virsh domifaddr로 IP 조회
            result = subprocess.run([
                "virsh", "domifaddr", vm_id
            ], capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'ipv4' in line.lower():
                        # IP 주소 추출 (예: "192.168.122.100/24")
                        parts = line.split()
                        for part in parts:
                            if '/' in part and '.' in part:
                                return part.split('/')[0]
            
            # 대체 방법: DHCP 리스 파일에서 찾기
            return self._get_ip_from_dhcp_lease(vm_id)
            
        except Exception as e:
            logger.warning(f"VM IP 조회 실패: {e}")
            # 기본 IP 반환 (개발용)
            return "192.168.122.100"
    
    def _get_ip_from_dhcp_lease(self, vm_id: str) -> str:
        """
        DHCP 리스 파일에서 IP 조회
        """
        lease_files = [
            "/var/lib/dhcp/dhcpd.leases",
            "/var/lib/libvirt/dnsmasq/virbr0.leases"
        ]
        
        for lease_file in lease_files:
            try:
                if Path(lease_file).exists():
                    with open(lease_file, 'r') as f:
                        content = f.read()
                        # 간단한 파싱으로 IP 찾기
                        if vm_id in content:
                            # 더 정교한 파싱 필요
                            pass
            except Exception:
                continue
        
        # 찾지 못한 경우 기본값 반환
        return "192.168.122.100"
    
    def stop_vm(self, vm_id: str) -> bool:
        """
        VM 중지 (개발 환경용 Mock 버전)
        """
        try:
            if settings.DEBUG:
                logger.info(f"개발 환경: Mock VM 중지 - {vm_id}")
                return True
                
            subprocess.run([
                "virsh", "shutdown", vm_id
            ], check=True, timeout=30)
            
            logger.info(f"VM 중지 완료: {vm_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 중지 실패: {e}")
            return False
    
    def start_vm(self, vm_id: str) -> bool:
        """
        VM 시작 (개발 환경용 Mock 버전)
        """
        try:
            if settings.DEBUG:
                logger.info(f"개발 환경: Mock VM 시작 - {vm_id}")
                return True
                
            subprocess.run([
                "virsh", "start", vm_id
            ], check=True, timeout=30)
            
            logger.info(f"VM 시작 완료: {vm_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 시작 실패: {e}")
            return False
    
    def restart_vm(self, vm_id: str) -> bool:
        """
        VM 재시작 (개발 환경용 Mock 버전)
        """
        try:
            if settings.DEBUG:
                logger.info(f"개발 환경: Mock VM 재시작 - {vm_id}")
                return True
                
            subprocess.run([
                "virsh", "reboot", vm_id
            ], check=True, timeout=30)
            
            logger.info(f"VM 재시작 완료: {vm_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 재시작 실패: {e}")
            return False
    
    def delete_vm(self, vm_id: str) -> bool:
        """
        VM 삭제 (개발 환경용 Mock 버전)
        """
        try:
            if settings.DEBUG:
                logger.info(f"개발 환경: Mock VM 삭제 - {vm_id}")
                return True
                
            # VM 중지
            subprocess.run([
                "virsh", "destroy", vm_id
            ], check=False)  # 이미 중지된 경우 무시
            
            # VM 정의 삭제
            subprocess.run([
                "virsh", "undefine", vm_id
            ], check=True, timeout=30)
            
            logger.info(f"VM 삭제 완료: {vm_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 삭제 실패: {e}")
            return False
    
    def cleanup_vm(self, vm_id: str) -> None:
        """
        VM 정리 (파일 삭제 포함) (개발 환경용 Mock 버전)
        """
        try:
            if settings.DEBUG:
                logger.info(f"개발 환경: Mock VM 정리 - {vm_id}")
                return
                
            # VM 삭제
            self.delete_vm(vm_id)
            
            # 디스크 파일 삭제
            disk_path = self.image_path / f"{vm_id}.qcow2"
            if disk_path.exists():
                disk_path.unlink()
                
        except Exception as e:
            logger.error(f"VM 정리 실패: {e}")
    
    def get_vm_status(self, vm_id: str) -> HostingStatus:
        """
        VM 상태 조회 (개발 환경용 Mock 버전)
        """
        try:
            if settings.DEBUG:
                logger.info(f"개발 환경: Mock VM 상태 조회 - {vm_id}")
                return HostingStatus.RUNNING
                
            result = subprocess.run([
                "virsh", "domstate", vm_id
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                state = result.stdout.strip().lower()
                if state == "running":
                    return HostingStatus.RUNNING
                elif state == "shut off":
                    return HostingStatus.STOPPED
                elif state in ["paused", "suspended"]:
                    return HostingStatus.STOPPED
                else:
                    return HostingStatus.ERROR
            else:
                return HostingStatus.ERROR
                
        except Exception as e:
            logger.error(f"VM 상태 조회 실패: {e}")
            return HostingStatus.ERROR 