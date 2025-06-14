"""
VM 관리 서비스 - VM 생성, 관리, 운영 로직
"""
import uuid
import subprocess
import logging
import xml.etree.ElementTree as ET
import yaml
import base64
from typing import Optional, Dict, List
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import VMOperationError
from app.models.hosting import HostingStatus

# 로깅 설정
logger = logging.getLogger(__name__)

class VMService:
    """VM 관리 서비스 클래스"""
    
    def __init__(self):
        self.bridge_name = settings.VM_BRIDGE_NAME
        self.image_path = Path(settings.VM_IMAGE_PATH)
        self.template_image = settings.VM_TEMPLATE_IMAGE
    
    def generate_vm_id(self) -> str:
        """
        고유한 VM ID 생성
        """
        return f"vm-{uuid.uuid4().hex[:8]}"
    
    def get_available_ssh_port(self, start_port: int = None, end_port: int = None) -> int:
        """
        사용 가능한 SSH 포트 찾기
        """
        start = start_port or settings.SSH_PORT_RANGE_START
        end = end_port or settings.SSH_PORT_RANGE_END
        
        for port in range(start, end + 1):
            if self._is_port_available(port):
                return port
        
        raise VMOperationError(f"사용 가능한 SSH 포트가 없습니다. (범위: {start}-{end})")
    
    def _is_port_available(self, port: int) -> bool:
        """
        포트 사용 가능 여부 확인
        """
        try:
            result = subprocess.run(
                ["netstat", "-an"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return f":{port}" not in result.stdout
        except Exception as e:
            logger.warning(f"포트 확인 중 오류: {e}")
            return True  # 확인할 수 없으면 사용 가능한 것으로 간주
    
    def create_cloud_init_config(self, vm_id: str, user_id: str) -> str:
        """
        cloud-init 설정 생성 (웹서버 자동 설치)
        """
        try:
            # cloud-init user-data 설정
            user_data = {
                'version': 1,
                'users': [
                    {
                        'name': 'ubuntu',
                        'sudo': 'ALL=(ALL) NOPASSWD:ALL',
                        'shell': '/bin/bash',
                        'ssh_authorized_keys': [
                            # TODO: SSH 키 관리 시스템 연동
                            'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... webhoster-default'
                        ]
                    }
                ],
                'package_update': True,
                'packages': [
                    'nginx',
                    'curl',
                    'wget',
                    'unzip',
                    'git'
                ],
                'runcmd': [
                    # Nginx 시작 및 활성화
                    'systemctl enable nginx',
                    'systemctl start nginx',
                    
                    # 기본 웹 페이지 생성
                    f'mkdir -p /var/www/html',
                    f'chown -R www-data:www-data /var/www/html',
                    f'chmod -R 755 /var/www/html',
                    
                    # 사용자별 환영 페이지 생성
                    f"""cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>웹 호스팅 서비스 - {user_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
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
        }}
        .welcome {{
            text-align: center;
            font-size: 1.2em;
            line-height: 1.6;
            margin-bottom: 40px;
        }}
        .info-box {{
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .upload-info {{
            background: rgba(46, 204, 113, 0.3);
            border-left: 4px solid #2ecc71;
        }}
        .ssh-info {{
            background: rgba(52, 152, 219, 0.3);
            border-left: 4px solid #3498db;
        }}
        code {{
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            font-size: 0.9em;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 웹 호스팅 서비스</h1>
        <div class="welcome">
            <p><strong>{user_id}</strong>님의 웹 호스팅이 성공적으로 생성되었습니다!</p>
            <p>VM ID: <code>{vm_id}</code></p>
        </div>
        
        <div class="info-box upload-info">
            <h3>📁 파일 업로드 방법</h3>
            <p>웹 파일을 업로드하려면 다음 경로를 사용하세요:</p>
            <p><code>/var/www/html/</code></p>
            <p>SFTP 또는 SCP를 사용하여 파일을 업로드할 수 있습니다.</p>
        </div>
        
        <div class="info-box ssh-info">
            <h3>🔐 SSH 접속 정보</h3>
            <p>SSH로 서버에 접속하여 직접 관리할 수 있습니다:</p>
            <p><code>ssh ubuntu@your-domain -p YOUR_SSH_PORT</code></p>
            <p>웹 서버 재시작: <code>sudo systemctl restart nginx</code></p>
        </div>
        
        <div class="info-box">
            <h3>📝 시작하기</h3>
            <p>1. 이 페이지를 교체하려면 <code>/var/www/html/index.html</code>을 수정하세요</p>
            <p>2. 정적 파일들을 <code>/var/www/html/</code>에 업로드하세요</p>
            <p>3. PHP나 다른 언어를 사용하려면 추가 설정이 필요합니다</p>
        </div>
        
        <div class="footer">
            <p>웹 호스팅 서비스 © 2024</p>
            <p>서버 시작 시간: $(date)</p>
        </div>
    </div>
</body>
</html>
EOF""",
                    
                    # Nginx 기본 설정 수정
                    'sed -i "s/# server_names_hash_bucket_size 64;/server_names_hash_bucket_size 64;/" /etc/nginx/nginx.conf',
                    
                    # 파일 권한 설정
                    'chown -R ubuntu:ubuntu /home/ubuntu',
                    'usermod -aG www-data ubuntu',
                    
                    # SSH 설정 개선
                    'sed -i "s/#PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config',
                    'systemctl reload ssh',
                    
                    # 방화벽 설정 (기본 포트만 허용)
                    'ufw --force enable',
                    'ufw allow ssh',
                    'ufw allow 80/tcp',
                    'ufw allow 443/tcp',
                    
                    # 완료 로그
                    f'echo "VM {vm_id} 설정 완료: $(date)" >> /var/log/webhoster-setup.log'
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
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # PHP 지원 (필요시)
    # location ~ \\.php$ {
    #     include snippets/fastcgi-php.conf;
    #     fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
    # }
    
    # 보안 설정
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}''',
                        'permissions': '0644'
                    }
                ],
                'final_message': f'VM {vm_id} 웹서버 설정이 완료되었습니다!'
            }
            
            # YAML로 변환
            user_data_yaml = yaml.dump(user_data, default_flow_style=False)
            
            # cloud-init 파일 생성
            cloud_init_dir = self.image_path / "cloud-init" / vm_id
            cloud_init_dir.mkdir(parents=True, exist_ok=True)
            
            # user-data 파일 저장
            user_data_file = cloud_init_dir / "user-data"
            with open(user_data_file, 'w') as f:
                f.write(f"#cloud-config\\n{user_data_yaml}")
            
            # meta-data 파일 생성
            meta_data = {
                'instance-id': vm_id,
                'local-hostname': vm_id
            }
            
            meta_data_file = cloud_init_dir / "meta-data"
            with open(meta_data_file, 'w') as f:
                f.write(yaml.dump(meta_data, default_flow_style=False))
            
            # cloud-init ISO 이미지 생성
            iso_path = cloud_init_dir / "cloud-init.iso"
            subprocess.run([
                "genisoimage", "-output", str(iso_path),
                "-volid", "cidata", "-joliet", "-rock",
                str(user_data_file), str(meta_data_file)
            ], check=True, timeout=60)
            
            logger.info(f"cloud-init 설정 생성 완료: {iso_path}")
            return str(iso_path)
            
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
                # 템플릿에서 복사
                subprocess.run([
                    "qemu-img", "create", "-f", "qcow2",
                    "-b", str(template_path),
                    "-F", "qcow2",
                    str(disk_path)
                ], check=True, timeout=60)
            else:
                # 새 이미지 생성
                subprocess.run([
                    "qemu-img", "create", "-f", "qcow2",
                    str(disk_path), f"{size_gb}G"
                ], check=True, timeout=60)
            
            logger.info(f"VM 디스크 생성 완료: {disk_path}")
            return str(disk_path)
            
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
        VM 생성 및 시작 (웹서버 자동 설치 포함)
        """
        try:
            # 1. 디스크 이미지 생성
            disk_path = self.create_vm_disk(vm_id)
            
            # 2. cloud-init 설정 생성 (웹서버 자동 설치)
            cloud_init_iso = None
            if user_id:
                try:
                    cloud_init_iso = self.create_cloud_init_config(vm_id, user_id)
                    logger.info(f"cloud-init 설정 생성 완료: {cloud_init_iso}")
                except Exception as e:
                    logger.warning(f"cloud-init 설정 생성 실패, 기본 설정으로 진행: {e}")
            
            # 3. VM XML 정의 생성
            vm_xml = self.create_vm_xml(vm_id, disk_path, ssh_port, cloud_init_iso)
            
            # 4. VM 정의 등록
            xml_file = f"/tmp/{vm_id}.xml"
            with open(xml_file, 'w') as f:
                f.write(vm_xml)
            
            # libvirt에 VM 정의
            subprocess.run([
                "virsh", "define", xml_file
            ], check=True, timeout=30)
            
            # 5. VM 시작
            subprocess.run([
                "virsh", "start", vm_id
            ], check=True, timeout=30)
            
            # 6. IP 주소 할당 대기 및 조회
            vm_ip = self.get_vm_ip(vm_id)
            
            logger.info(f"VM 생성 완료: {vm_id}, IP: {vm_ip}")
            
            return {
                "vm_id": vm_id,
                "vm_ip": vm_ip,
                "disk_path": disk_path,
                "cloud_init_iso": cloud_init_iso,
                "status": HostingStatus.RUNNING.value
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 생성 실패: {e}")
            # 실패 시 정리
            self.cleanup_vm(vm_id)
            raise VMOperationError(f"VM 생성에 실패했습니다: {e}")
        except Exception as e:
            logger.error(f"예상치 못한 VM 생성 오류: {e}")
            self.cleanup_vm(vm_id)
            raise VMOperationError(f"VM 생성 중 오류가 발생했습니다: {e}")
    
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
        VM 중지
        """
        try:
            subprocess.run([
                "virsh", "shutdown", vm_id
            ], check=True, timeout=30)
            
            logger.info(f"VM 중지 요청: {vm_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 중지 실패: {e}")
            raise VMOperationError(f"VM 중지에 실패했습니다: {e}")
    
    def start_vm(self, vm_id: str) -> bool:
        """
        VM 시작
        """
        try:
            subprocess.run([
                "virsh", "start", vm_id
            ], check=True, timeout=30)
            
            logger.info(f"VM 시작: {vm_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 시작 실패: {e}")
            raise VMOperationError(f"VM 시작에 실패했습니다: {e}")
    
    def restart_vm(self, vm_id: str) -> bool:
        """
        VM 재시작
        """
        try:
            subprocess.run([
                "virsh", "reboot", vm_id
            ], check=True, timeout=30)
            
            logger.info(f"VM 재시작: {vm_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 재시작 실패: {e}")
            raise VMOperationError(f"VM 재시작에 실패했습니다: {e}")
    
    def delete_vm(self, vm_id: str) -> bool:
        """
        VM 완전 삭제
        """
        try:
            # VM 중지
            try:
                subprocess.run([
                    "virsh", "destroy", vm_id
                ], timeout=30)
            except subprocess.CalledProcessError:
                pass  # 이미 중지된 경우 무시
            
            # VM 정의 제거
            subprocess.run([
                "virsh", "undefine", vm_id
            ], check=True, timeout=30)
            
            # 디스크 이미지 삭제
            disk_path = self.image_path / f"{vm_id}.qcow2"
            if disk_path.exists():
                disk_path.unlink()
            
            logger.info(f"VM 삭제 완료: {vm_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"VM 삭제 실패: {e}")
            raise VMOperationError(f"VM 삭제에 실패했습니다: {e}")
    
    def cleanup_vm(self, vm_id: str) -> None:
        """
        VM 정리 (오류 시 호출)
        """
        try:
            self.delete_vm(vm_id)
        except Exception as e:
            logger.error(f"VM 정리 중 오류: {e}")
    
    def get_vm_status(self, vm_id: str) -> HostingStatus:
        """
        VM 상태 조회
        """
        try:
            result = subprocess.run([
                "virsh", "domstate", vm_id
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                state = result.stdout.strip().lower()
                
                if state == "running":
                    return HostingStatus.RUNNING
                elif state in ["shut off", "shutoff"]:
                    return HostingStatus.STOPPED
                elif state in ["paused", "suspended"]:
                    return HostingStatus.STOPPING
                else:
                    return HostingStatus.ERROR
            else:
                return HostingStatus.ERROR
                
        except Exception as e:
            logger.error(f"VM 상태 조회 실패: {e}")
            return HostingStatus.ERROR 