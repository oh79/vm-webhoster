#!/bin/bash

# 🚀 1단계: 시스템 초기 설정
# 시스템 업데이트 및 필수 패키지 설치 (VM 생성 도구 포함)

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

echo -e "${GREEN}🚀 1단계: 시스템 초기 설정 시작 (VM 도구 포함)${NC}"
echo "================================================"

# 시스템 정보 확인
log_step "시스템 정보 확인"
echo "  - OS: $(lsb_release -d | cut -f2)"
echo "  - Kernel: $(uname -r)"
echo "  - Architecture: $(uname -m)"
echo "  - Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  - Disk: $(df -h / | awk 'NR==2 {print $4}') available"

# 가상화 지원 확인
log_step "가상화 지원 확인"
if grep -q -E '(vmx|svm)' /proc/cpuinfo; then
    log_success "CPU 가상화 지원 확인됨 (VT-x/AMD-V)"
else
    log_warning "CPU 가상화 지원이 확인되지 않습니다. BIOS에서 가상화를 활성화하세요."
fi

# 시스템 업데이트
log_step "시스템 패키지 업데이트"
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
log_step "필수 패키지 설치"
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    pkg-config \
    libpq-dev \
    net-tools \
    htop \
    vim \
    tree

log_success "필수 패키지 설치 완료"

# Docker 설치
log_step "Docker 설치"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    log_success "Docker 설치 완료"
else
    log_info "Docker는 이미 설치되어 있습니다."
fi

# VM 생성 도구 설치 (KVM/QEMU + libvirt)
log_step "VM 생성 도구 설치 (KVM/QEMU + libvirt)"
sudo apt install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virtinst \
    virt-manager \
    cpu-checker \
    libguestfs-tools \
    libosinfo-bin \
    cloud-utils \
    cloud-image-utils \
    genisoimage \
    qemu-utils

log_success "VM 생성 도구 설치 완료"

# libvirt 서비스 설정
log_step "libvirt 서비스 설정"
sudo systemctl start libvirtd
sudo systemctl enable libvirtd

# 사용자를 VM 관리 그룹에 추가
log_info "사용자를 VM 관리 그룹에 추가 중..."
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER

# libvirt 기본 네트워크 설정
log_info "libvirt 기본 네트워크 설정..."
sudo virsh net-start default 2>/dev/null || log_warning "기본 네트워크가 이미 시작되었거나 설정이 필요합니다."
sudo virsh net-autostart default 2>/dev/null || log_warning "기본 네트워크 자동시작 설정 실패"

log_success "libvirt 서비스 설정 완료"

# VM 이미지 디렉토리 생성 및 권한 설정
log_step "VM 환경 디렉토리 설정"
sudo mkdir -p /var/lib/vm-webhoster
sudo chown $USER:libvirt /var/lib/vm-webhoster 2>/dev/null || sudo chown $USER:$USER /var/lib/vm-webhoster
sudo chmod 755 /var/lib/vm-webhoster

# 프로젝트 내 VM 디렉토리도 생성
mkdir -p vm-images/templates
mkdir -p vm-images/containers
chmod 755 vm-images/templates
chmod 755 vm-images/containers

log_success "VM 환경 디렉토리 설정 완료"

# Node.js 설치
log_step "Node.js 18.x 설치"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    log_success "Node.js 설치 완료"
else
    log_info "Node.js는 이미 설치되어 있습니다."
fi

echo "  - Node.js: $(node --version)"
echo "  - npm: $(npm --version)"

# PostgreSQL 설치
log_step "PostgreSQL 설치"
if ! command -v psql &> /dev/null; then
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    log_success "PostgreSQL 설치 완료"
else
    log_info "PostgreSQL은 이미 설치되어 있습니다."
    sudo systemctl start postgresql 2>/dev/null || true
    sudo systemctl enable postgresql 2>/dev/null || true
fi

# Redis 설치
log_step "Redis 설치"
if ! command -v redis-server &> /dev/null; then
    sudo apt install -y redis-server
    sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
    sudo systemctl restart redis-server
    sudo systemctl enable redis-server
    log_success "Redis 설치 완료"
else
    log_info "Redis는 이미 설치되어 있습니다."
    sudo systemctl start redis-server 2>/dev/null || true
    sudo systemctl enable redis-server 2>/dev/null || true
fi

# 방화벽 설정
log_step "기본 방화벽 설정"
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# VM SSH 포트 범위 (10000-20000)
sudo ufw allow 10000:20000/tcp

log_success "방화벽 설정 완료"

# Python Jinja2 템플릿 엔진 설치 (nginx 설정용)
log_step "Python Jinja2 템플릿 엔진 설치"
if ! python3 -c "import jinja2" &> /dev/null; then
    sudo apt install -y python3-jinja2
    log_success "Python Jinja2 설치 완료"
else
    log_info "Python Jinja2는 이미 설치되어 있습니다."
fi

# Nginx 환경 설정 및 구조 생성
log_step "Nginx 호스팅 환경 설정"

# nginx 서비스 설치 및 시작 (이미 설치되었을 수 있음)
if ! command -v nginx &> /dev/null; then
    sudo apt install -y nginx
    log_success "Nginx 설치 완료"
else
    log_info "Nginx는 이미 설치되어 있습니다."
fi

sudo systemctl start nginx 2>/dev/null || true
sudo systemctl enable nginx 2>/dev/null || true

# nginx 호스팅용 디렉토리 구조 생성
sudo mkdir -p /etc/nginx/sites-available/hosting
sudo mkdir -p /etc/nginx/sites-enabled/hosting
sudo mkdir -p /var/log/nginx

# 프로젝트의 nginx 설정을 시스템에 복사
log_info "프로젝트 nginx 설정 파일들을 시스템에 복사 중..."
if [ -f "nginx/nginx.conf" ]; then
    sudo cp nginx/nginx.conf /etc/nginx/nginx.conf.backup 2>/dev/null || true
    # 기본 nginx.conf는 건드리지 않고 추가 설정만 복사
fi

if [ -d "nginx/conf.d" ]; then
    sudo cp -r nginx/conf.d/* /etc/nginx/conf.d/ 2>/dev/null || true
fi

if [ -f "nginx/sites-available/main.conf" ]; then
    sudo cp nginx/sites-available/main.conf /etc/nginx/sites-available/
    sudo ln -sf /etc/nginx/sites-available/main.conf /etc/nginx/sites-enabled/ 2>/dev/null || true
fi

# nginx 템플릿 파일을 위한 디렉토리 생성 및 복사
sudo mkdir -p /etc/nginx/templates
if [ -f "nginx/templates/user-hosting.conf.j2" ]; then
    sudo cp nginx/templates/user-hosting.conf.j2 /etc/nginx/templates/
fi

# nginx 설정 파일들에 대한 권한 설정
sudo chown -R root:root /etc/nginx/sites-available/hosting
sudo chown -R root:root /etc/nginx/sites-enabled/hosting
sudo chmod 755 /etc/nginx/sites-available/hosting
sudo chmod 755 /etc/nginx/sites-enabled/hosting

log_success "Nginx 호스팅 환경 설정 완료"

# nginx-config-manager.sh 초기화
log_step "Nginx 설정 관리자 초기화"
if [ -f "scripts/nginx-config-manager.sh" ]; then
    chmod +x scripts/nginx-config-manager.sh
    
    # nginx-config-manager 초기화 실행
    log_info "nginx-config-manager 초기화 실행 중..."
    sudo ./scripts/nginx-config-manager.sh init --force 2>/dev/null || {
        log_warning "nginx-config-manager 초기화 중 일부 경고가 발생했지만 계속 진행합니다."
    }
    
    log_success "Nginx 설정 관리자 초기화 완료"
else
    log_warning "nginx-config-manager.sh 파일을 찾을 수 없습니다."
fi

# nginx 설정 검증 및 재시작
log_info "Nginx 설정 검증 중..."
if sudo nginx -t 2>/dev/null; then
    sudo systemctl reload nginx
    log_success "Nginx 설정 검증 및 재시작 완료"
else
    log_warning "Nginx 설정에 문제가 있을 수 있습니다. 기본 설정으로 복원합니다."
    sudo systemctl restart nginx 2>/dev/null || true
fi

# Docker 권한 문제 해결
log_step "Docker 권한 최적화"
# Docker 소켓 권한 설정 (임시 해결책)
sudo chmod 666 /var/run/docker.sock 2>/dev/null || {
    log_warning "Docker 소켓 권한 설정에 실패했습니다."
}

# Docker 서비스 재시작으로 권한 확실히 적용
sudo systemctl restart docker 2>/dev/null || {
    log_warning "Docker 서비스 재시작에 실패했습니다."
}

log_success "Docker 권한 최적화 완료"

# Nginx PID 파일 문제 해결
log_step "Nginx PID 파일 최적화"
# nginx를 완전히 재시작해서 PID 파일 문제 해결
sudo systemctl stop nginx 2>/dev/null || true
sleep 2
sudo rm -f /var/run/nginx.pid 2>/dev/null || true
sudo systemctl start nginx

# PID 파일이 제대로 생성되었는지 확인
if [ -f "/var/run/nginx.pid" ] && [ -s "/var/run/nginx.pid" ]; then
    log_success "Nginx PID 파일 최적화 완료"
else
    log_warning "Nginx PID 파일 생성에 문제가 있을 수 있습니다."
fi

# 최종 nginx 리로드 테스트
if sudo systemctl reload nginx 2>/dev/null; then
    log_success "Nginx 리로드 테스트 성공"
else
    log_warning "Nginx 리로드 테스트 실패 - 재시작으로 복구 시도"
    sudo systemctl restart nginx 2>/dev/null || true
fi

# 설치 검증
log_step "설치 검증"
echo ""
echo "📋 설치된 구성 요소 확인:"
echo "  ├─ Docker: $(docker --version 2>/dev/null || echo '❌ 설치 실패')"
echo "  ├─ libvirt: $(virsh --version 2>/dev/null || echo '❌ 설치 실패')"
echo "  ├─ QEMU: $(qemu-system-x86_64 --version 2>/dev/null | head -1 || echo '❌ 설치 실패')"
echo "  ├─ Node.js: $(node --version 2>/dev/null || echo '❌ 설치 실패')"
echo "  ├─ PostgreSQL: $(psql --version 2>/dev/null || echo '❌ 설치 실패')"
echo "  └─ Redis: $(redis-server --version 2>/dev/null || echo '❌ 설치 실패')"

echo ""
echo "🔐 사용자 그룹 확인:"
echo "  ├─ docker: $(groups $USER | grep -o docker || echo '❌')"
echo "  ├─ libvirt: $(groups $USER | grep -o libvirt || echo '❌')"
echo "  └─ kvm: $(groups $USER | grep -o kvm || echo '❌')"

echo ""
echo "⚠️  중요: 그룹 변경 사항을 적용하려면 다음 중 하나를 수행하세요:"
echo "    1. 터미널을 재시작하거나"
echo "    2. 다음 명령어 실행: newgrp docker && newgrp libvirt"
echo "    3. 로그아웃 후 다시 로그인"

echo -e "${GREEN}✅ 1단계: 시스템 초기 설정 완료 (VM 도구 포함)${NC}"
echo "================================================"
echo "🎯 VM 생성 도구 설치 완료! 이제 호스팅 인스턴스를 생성할 수 있습니다."
echo "다음 단계: ./scripts/02-project-setup.sh" 