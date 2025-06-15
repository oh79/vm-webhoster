#!/bin/bash

# 🐳 Docker 권한 및 그룹 설정 스크립트
# Docker 소켓 접근 권한과 필요한 그룹들을 설정합니다

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

echo -e "${GREEN}🐳 Docker 권한 및 그룹 설정 스크립트${NC}"
echo "=========================================="

# 현재 사용자 확인
CURRENT_USER=$(whoami)
log_info "현재 사용자: $CURRENT_USER"

# Docker 서비스 상태 확인
log_info "Docker 서비스 상태 확인 중..."
if systemctl is-active --quiet docker; then
    log_success "Docker 서비스가 실행 중입니다"
else
    log_info "Docker 서비스 시작 중..."
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# 사용자를 docker 그룹에 추가
log_info "사용자를 docker 그룹에 추가 중..."
sudo usermod -aG docker $CURRENT_USER

# 사용자를 libvirt 그룹에 추가 (이미 추가되었지만 확인)
log_info "사용자를 libvirt 그룹에 추가 중..."
sudo usermod -aG libvirt $CURRENT_USER
sudo usermod -aG kvm $CURRENT_USER

# Docker 소켓 권한 확인
log_info "Docker 소켓 권한 확인 중..."
if [ -S /var/run/docker.sock ]; then
    sudo chmod 666 /var/run/docker.sock
    log_success "Docker 소켓 권한 설정 완료"
else
    log_error "Docker 소켓을 찾을 수 없습니다"
fi

# 그룹 변경사항 즉시 적용
log_info "그룹 변경사항 즉시 적용 중..."
exec sudo -u $CURRENT_USER newgrp docker << 'EOF'

# Docker 접근 테스트
echo -e "\033[0;34m[INFO]\033[0m Docker 접근 테스트 중..."
if docker ps > /dev/null 2>&1; then
    echo -e "\033[0;32m[SUCCESS]\033[0m Docker 접근 가능"
else
    echo -e "\033[0;31m[ERROR]\033[0m Docker 접근 실패"
    exit 1
fi

# libvirt 접근 테스트  
echo -e "\033[0;34m[INFO]\033[0m libvirt 접근 테스트 중..."
if virsh --version > /dev/null 2>&1; then
    echo -e "\033[0;32m[SUCCESS]\033[0m libvirt 접근 가능"
else
    echo -e "\033[0;31m[ERROR]\033[0m libvirt 접근 실패"
fi

echo ""
echo -e "\033[0;32m✅ 권한 설정 완료!\033[0m"
echo ""
echo -e "\033[1;33m📋 설정된 그룹:\033[0m"
groups

echo ""
echo -e "\033[1;33m🎯 다음 단계:\033[0m"
echo "  1. 백엔드 서비스 재시작"
echo "  2. 브라우저에서 호스팅 생성 테스트"

EOF 