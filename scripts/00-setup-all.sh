#!/bin/bash

# 🚀 웹 호스팅 서비스 로컬 개발 환경 설치 스크립트
# Ubuntu 22.04 LTS Clean 환경 → 로컬 개발 환경
# 실행: chmod +x scripts/00-setup-all.sh && ./scripts/00-setup-all.sh

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_cmd() {
    echo -e "${CYAN}[CMD]${NC} $1"
}

# 진행률 표시
show_progress() {
    local current=$1
    local total=$2
    local desc=$3
    local percent=$((current * 100 / total))
    echo -e "${CYAN}[${current}/${total}] (${percent}%)${NC} ${desc}"
}

# 스크립트 시작
clear
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🚀 웹 호스팅 서비스 로컬 개발 환경 설치          ║"
echo "║                                                              ║"
echo "║  Ubuntu 22.04 Clean → 로컬 개발 환경                          ║"
echo "║  예상 소요 시간: 15-20분                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 사용자 확인
read -p "계속 진행하시겠습니까? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    log_info "설치가 취소되었습니다."
    exit 0
fi

# 총 단계 수
TOTAL_STEPS=18
CURRENT_STEP=0

# Step 1: 시스템 정보 확인
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "시스템 정보 확인"

log_info "시스템 정보:"
echo "  - OS: $(lsb_release -d | cut -f2)"
echo "  - Kernel: $(uname -r)"
echo "  - Architecture: $(uname -m)"
echo "  - Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  - Disk: $(df -h / | awk 'NR==2 {print $4}') available"

# 최소 요구사항 확인
total_memory_gb=$(free -g | awk '/^Mem:/{print $2}')
available_space_gb=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')

if [ "$total_memory_gb" -lt 4 ]; then
    log_warning "메모리가 부족할 수 있습니다. (현재: ${total_memory_gb}GB, 권장: 4GB+)"
fi

if [ "$available_space_gb" -lt 20 ]; then
    log_warning "디스크 공간이 부족할 수 있습니다. (현재: ${available_space_gb}GB, 권장: 20GB+)"
fi

# Step 2: 시스템 업데이트
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "시스템 패키지 업데이트"

log_cmd "sudo apt update && sudo apt upgrade -y"
sudo apt update && sudo apt upgrade -y

# Step 3: 필수 패키지 설치
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "필수 패키지 설치"

log_cmd "필수 패키지 설치 중..."
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
    libpq-dev

log_success "필수 패키지 설치 완료"

# Step 4: PostgreSQL 설치
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "PostgreSQL 데이터베이스 설치"

log_info "PostgreSQL 설치 중..."
sudo apt install -y postgresql postgresql-contrib

log_info "PostgreSQL 서비스 시작 및 활성화..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

log_info "데이터베이스 및 사용자 생성..."
sudo -u postgres psql << EOF
CREATE DATABASE webhoster_db;
CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';
GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;
ALTER USER webhoster_user CREATEDB;
\q
EOF

log_success "PostgreSQL 설치 및 설정 완료"

# Step 5: Redis 설치
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Redis 캐시 서버 설치"

log_info "Redis 설치 중..."
sudo apt install -y redis-server

log_info "Redis 설정..."
sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf

log_info "Redis 서비스 시작 및 활성화..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

log_success "Redis 설치 및 설정 완료"

# Step 6: Node.js 설치
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Node.js 및 npm 설치"

log_info "Node.js 18.x 저장소 추가..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

log_info "Node.js 설치..."
sudo apt install -y nodejs

log_info "설치된 버전 확인:"
echo "  - Node.js: $(node --version)"
echo "  - npm: $(npm --version)"

log_success "Node.js 설치 완료"

# Step 7: KVM/QEMU 설치 (VM 호스팅용)
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "KVM/QEMU 가상화 환경 설치"

log_info "가상화 지원 확인..."
if grep -q -E '(vmx|svm)' /proc/cpuinfo; then
    log_success "CPU 가상화 지원 확인됨"
else
    log_warning "CPU 가상화 지원이 확인되지 않습니다. BIOS에서 활성화하세요."
fi

log_info "KVM/QEMU 패키지 설치..."
sudo apt install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virtinst \
    virt-manager \
    cpu-checker \
    libguestfs-tools \
    libosinfo-bin

log_success "KVM/QEMU 설치 완료"

# Step 8: libvirt 설정
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "libvirt 서비스 설정"

log_info "libvirt 서비스 시작 및 활성화..."
sudo systemctl start libvirtd
sudo systemctl enable libvirtd

log_info "사용자를 libvirt 그룹에 추가..."
sudo usermod -aG libvirt $USER

log_info "기본 네트워크 확인..."
sudo virsh net-start default 2>/dev/null || true
sudo virsh net-autostart default

log_success "libvirt 설정 완료"

# Step 9: Nginx 설치 (프록시용)
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Nginx 웹서버 설치"

log_info "Nginx 설치..."
sudo apt install -y nginx

log_info "Nginx 서비스 시작 및 활성화..."
sudo systemctl start nginx
sudo systemctl enable nginx

log_success "Nginx 설치 완료"

# Step 10: 프로젝트 디렉토리 확인 및 생성
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "프로젝트 환경 설정"

log_info "필요한 디렉토리 생성..."
mkdir -p nginx/static
mkdir -p nginx-configs
mkdir -p scripts
mkdir -p logs
mkdir -p backend/uploads
mkdir -p backend/vm-images
mkdir -p backups

log_info "권한 설정..."
chmod 755 nginx/static
chmod 755 logs
chmod 755 backend/uploads
chmod 755 backend/vm-images

log_success "프로젝트 환경 설정 완료"

# Step 11: 환경 변수 설정
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "환경 변수 설정"

if [ -f "local.env" ]; then
    log_info "local.env에서 .env로 환경 변수 복사..."
    cp local.env .env
    cp local.env backend/.env
    log_success "환경 변수 파일 복사 완료"
else
    log_error "local.env 파일을 찾을 수 없습니다."
    exit 1
fi

# Step 12: Python 가상환경 설정
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Python 백엔드 환경 설정"

log_info "Python 가상환경 생성..."
cd backend
python3 -m venv venv

log_info "가상환경 활성화 및 패키지 설치..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

log_success "Python 백엔드 환경 설정 완료"
cd ..

# Step 13: 프론트엔드 의존성 설치
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "프론트엔드 환경 설정"

log_info "프론트엔드 의존성 설치..."
cd frontend
npm install

log_success "프론트엔드 환경 설정 완료"
cd ..

# Step 14: 데이터베이스 마이그레이션
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "데이터베이스 마이그레이션"

log_info "데이터베이스 마이그레이션 실행..."
cd backend
source venv/bin/activate
python -m alembic upgrade head
cd ..

log_success "데이터베이스 마이그레이션 완료"

# Step 15: Ubuntu Cloud 이미지 다운로드
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Ubuntu Cloud 이미지 준비"

CLOUD_IMAGE_URL="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
CLOUD_IMAGE_PATH="./backend/vm-images/ubuntu-22.04-cloud.qcow2"

if [ ! -f "$CLOUD_IMAGE_PATH" ]; then
    log_info "Ubuntu 22.04 Cloud 이미지 다운로드 중..."
    wget -O "$CLOUD_IMAGE_PATH" "$CLOUD_IMAGE_URL"
    log_success "Ubuntu Cloud 이미지 다운로드 완료"
else
    log_info "Ubuntu Cloud 이미지가 이미 존재합니다."
fi

# Step 16: 로컬 실행 스크립트 생성
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "실행 스크립트 생성"

# 백엔드 실행 스크립트
cat > scripts/start-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 백엔드 서버 시작 중..."
cd backend
source venv/bin/activate
export $(cat .env | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF

# 프론트엔드 실행 스크립트
cat > scripts/start-frontend.sh << 'EOF'
#!/bin/bash
echo "🚀 프론트엔드 서버 시작 중..."
cd frontend
npm run dev
EOF

# 전체 서비스 실행 스크립트
cat > scripts/start-all.sh << 'EOF'
#!/bin/bash
echo "🚀 모든 서비스 시작 중..."

# 백엔드 백그라운드 실행
echo "백엔드 서버 시작..."
cd backend
source venv/bin/activate
export $(cat .env | xargs)
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "백엔드 PID: $BACKEND_PID"
cd ..

# 잠시 대기
sleep 3

# 프론트엔드 실행
echo "프론트엔드 서버 시작..."
cd frontend
npm run dev
EOF

# 서비스 중지 스크립트
cat > scripts/stop-all.sh << 'EOF'
#!/bin/bash
echo "🛑 모든 서비스 중지 중..."

# 백엔드 프로세스 종료
pkill -f "uvicorn app.main:app"

# 프론트엔드 프로세스 종료
pkill -f "next-server"

echo "모든 서비스가 중지되었습니다."
EOF

# 실행 권한 부여
chmod +x scripts/start-backend.sh
chmod +x scripts/start-frontend.sh
chmod +x scripts/start-all.sh
chmod +x scripts/stop-all.sh

log_success "실행 스크립트 생성 완료"

# Step 17: 서비스 상태 확인
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "서비스 상태 확인"

log_info "설치된 서비스 상태 확인..."

# PostgreSQL 상태 확인
if systemctl is-active --quiet postgresql; then
    log_success "PostgreSQL: 실행 중"
else
    log_error "PostgreSQL: 실행 실패"
fi

# Redis 상태 확인
if systemctl is-active --quiet redis-server; then
    log_success "Redis: 실행 중"
else
    log_error "Redis: 실행 실패"
fi

# Nginx 상태 확인
if systemctl is-active --quiet nginx; then
    log_success "Nginx: 실행 중"
else
    log_error "Nginx: 실행 실패"
fi

# libvirt 상태 확인
if systemctl is-active --quiet libvirtd; then
    log_success "libvirt: 실행 중"
else
    log_error "libvirt: 실행 실패"
fi

# Step 18: 설치 완료
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "설치 완료"

# 설치 완료 메시지
clear
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 로컬 개발 환경 설치 완료!               ║"
echo "║                                                              ║"
echo "║  웹 호스팅 서비스 로컬 개발 환경이 성공적으로 설치되었습니다!    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo
log_success "🚀 웹 호스팅 서비스 로컬 개발 환경 설치가 완료되었습니다!"
echo
log_info "📋 서비스 실행 방법:"
echo "   • 🔧 백엔드만 실행: ./scripts/start-backend.sh"
echo "   • 🎨 프론트엔드만 실행: ./scripts/start-frontend.sh"
echo "   • 🚀 모든 서비스 실행: ./scripts/start-all.sh"
echo "   • 🛑 모든 서비스 중지: ./scripts/stop-all.sh"
echo
log_info "🌐 서비스 접속 정보:"
echo "   • 프론트엔드: http://localhost:3000"
echo "   • 백엔드 API: http://localhost:8000"
echo "   • API 문서: http://localhost:8000/docs"
echo "   • 헬스체크: http://localhost:8000/api/v1/health"
echo
log_info "🗄️ 데이터베이스 정보:"
echo "   • PostgreSQL: localhost:5432 (webhoster_db)"
echo "   • Redis: localhost:6379"
echo "   • 사용자: webhoster_user / webhoster_pass"
echo
log_info "🔧 개발 도구:"
echo "   • 백엔드 로그: tail -f logs/backend.log"
echo "   • 데이터베이스 접속: psql -h localhost -U webhoster_user -d webhoster_db"
echo "   • Redis 접속: redis-cli"
echo
log_info "🎯 개발 시작하기:"
echo "   1. 새 터미널에서: ./scripts/start-backend.sh"
echo "   2. 또 다른 터미널에서: ./scripts/start-frontend.sh"
echo "   3. 브라우저에서 http://localhost:3000 접속"
echo

log_warning "⚠️  중요 안내:"
echo "   • 새 터미널을 열거나 다음 명령어를 실행하여 그룹 권한을 적용하세요:"
echo "     newgrp libvirt"
echo "   • 또는 시스템을 재부팅하세요."
echo

log_success "🎉 로컬 개발 환경 설치가 완료되었습니다!"
echo
echo -e "${CYAN}📖 다음 단계: ./scripts/start-all.sh 실행하여 서비스 시작${NC}"
echo 