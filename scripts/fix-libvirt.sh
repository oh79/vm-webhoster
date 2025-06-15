#!/bin/bash

# 🛠️ libvirt 및 VM 도구 설치 스크립트
# virsh, libvirt, QEMU/KVM 도구들을 설치합니다

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${GREEN}🛠️ libvirt 및 VM 도구 설치 스크립트${NC}"
echo "======================================"

# libvirt 및 QEMU/KVM 도구 설치
log_info "libvirt, QEMU/KVM 도구 설치 중..."

sudo apt-get update -qq
sudo apt-get install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virtinst \
    virt-manager \
    cloud-utils \
    cloud-image-utils \
    genisoimage \
    libguestfs-tools

log_success "libvirt 및 QEMU/KVM 도구 설치 완료"

# 사용자를 libvirt 그룹에 추가
log_info "사용자를 libvirt 그룹에 추가 중..."
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER

# libvirt 서비스 시작 및 활성화
log_info "libvirt 서비스 시작 중..."
sudo systemctl enable libvirtd
sudo systemctl start libvirtd

# 서비스 상태 확인
if systemctl is-active --quiet libvirtd; then
    log_success "libvirtd 서비스 실행 중"
else
    log_error "libvirtd 서비스 시작 실패"
    exit 1
fi

# virsh 명령어 테스트
log_info "virsh 명령어 테스트 중..."
if virsh --version > /dev/null 2>&1; then
    VIRSH_VERSION=$(virsh --version)
    log_success "virsh 설치 확인됨 (버전: $VIRSH_VERSION)"
else
    log_error "virsh 명령어를 찾을 수 없습니다"
    exit 1
fi

# 네트워크 설정 확인
log_info "libvirt 기본 네트워크 확인 중..."
if virsh net-list --all | grep -q "default"; then
    # 기본 네트워크가 있으면 시작
    virsh net-start default 2>/dev/null || true
    virsh net-autostart default 2>/dev/null || true
    log_success "libvirt 기본 네트워크 활성화됨"
else
    log_warning "libvirt 기본 네트워크를 찾을 수 없습니다"
fi

# 테스트용 네트워크 브리지 생성 (필요시)
log_info "VM 관리용 디렉토리 생성 중..."
sudo mkdir -p /var/lib/vm-webhoster
sudo chown $USER:libvirt /var/lib/vm-webhoster
sudo chmod 755 /var/lib/vm-webhoster

# VM 이미지 저장소 생성
mkdir -p ~/vm-webhoster/vm-images/templates
mkdir -p ~/vm-webhoster/vm-images/containers

log_success "VM 관리 환경 설정 완료"

echo ""
echo "✅ libvirt 설치 및 설정 완료!"
echo ""
echo "📋 설치된 구성요소:"
echo "  ├─ virsh: $(virsh --version)"
echo "  ├─ qemu-kvm: $(kvm --version | head -1)"
echo "  ├─ libvirtd: $(systemctl is-active libvirtd)"
echo "  └─ 사용자 그룹: libvirt, kvm"

echo ""
echo "⚠️  중요: 그룹 변경 사항을 적용하려면 다음 중 하나를 수행하세요:"
echo "  1. 터미널을 재시작하거나"
echo "  2. 다음 명령어 실행: newgrp libvirt"
echo ""
echo "🎯 다음 단계:"
echo "  1. 터미널 재시작 또는 newgrp libvirt 실행"
echo "  2. ./scripts/04-database-init.sh 실행 (마이그레이션)"
echo "  3. 서비스 재시작" 