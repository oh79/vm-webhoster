"""
VM 관리 서비스 - VM 생성, 관리, 운영 로직
"""
import uuid
import subprocess
import logging
import xml.etree.ElementTree as ET
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
    
    def create_vm_xml(self, vm_id: str, disk_path: str, ssh_port: int, memory_mb: int = 1024, vcpus: int = 1) -> str:
        """
        VM XML 정의 생성
        """
        # 기본 네트워크 인터페이스 MAC 주소 생성
        mac_address = self._generate_mac_address()
        
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
    </disk>
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
    
    def create_vm(self, vm_id: str, ssh_port: int) -> Dict[str, str]:
        """
        VM 생성 및 시작
        """
        try:
            # 1. 디스크 이미지 생성
            disk_path = self.create_vm_disk(vm_id)
            
            # 2. VM XML 정의 생성
            vm_xml = self.create_vm_xml(vm_id, disk_path, ssh_port)
            
            # 3. VM 정의 등록
            xml_file = f"/tmp/{vm_id}.xml"
            with open(xml_file, 'w') as f:
                f.write(vm_xml)
            
            # libvirt에 VM 정의
            subprocess.run([
                "virsh", "define", xml_file
            ], check=True, timeout=30)
            
            # 4. VM 시작
            subprocess.run([
                "virsh", "start", vm_id
            ], check=True, timeout=30)
            
            # 5. IP 주소 할당 대기 및 조회
            vm_ip = self.get_vm_ip(vm_id)
            
            logger.info(f"VM 생성 완료: {vm_id}, IP: {vm_ip}")
            
            return {
                "vm_id": vm_id,
                "vm_ip": vm_ip,
                "disk_path": disk_path,
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