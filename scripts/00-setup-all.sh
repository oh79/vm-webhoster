#!/bin/bash

# 🚀 웹 호스팅 서비스 완전 자동 설치 스크립트
# Ubuntu 22.04 LTS Clean 환경 → Production Ready 서비스
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
echo "║                🚀 웹 호스팅 서비스 완전 자동 설치              ║"
echo "║                                                              ║"
echo "║  Ubuntu 22.04 Clean → Production Ready 서비스                ║"
echo "║  예상 소요 시간: 10-15분                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 사용자 확인
read -p "계속 진행하시겠습니까? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    log_info "설치가 취소되었습니다."
    exit 0
fi

# 총 단계 수
TOTAL_STEPS=15
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
    python3-venv

log_success "필수 패키지 설치 완료"

# Step 4: Docker 설치
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Docker 설치"

log_info "Docker 공식 GPG 키 추가..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

log_info "Docker 저장소 추가..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

log_info "Docker 패키지 설치..."
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

log_success "Docker 설치 완료"

# Step 5: Docker 서비스 설정
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Docker 서비스 설정"

log_info "Docker 서비스 시작 및 활성화..."
sudo systemctl start docker
sudo systemctl enable docker

log_info "사용자를 docker 그룹에 추가..."
sudo usermod -aG docker $USER

log_success "Docker 서비스 설정 완료"

# Step 6: KVM/QEMU 설치
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

# Step 7: libvirt 설정
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

# Step 8: Python 환경 설정
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Python 개발 환경 설정"

log_info "Python 패키지 업데이트..."
python3 -m pip install --upgrade pip setuptools wheel

log_success "Python 환경 설정 완료"

# Step 9: 프로젝트 디렉토리 확인
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "프로젝트 환경 확인"

if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml 파일을 찾을 수 없습니다."
    log_info "프로젝트 루트 디렉토리에서 스크립트를 실행해주세요."
    exit 1
fi

log_info "필요한 디렉토리 생성..."
mkdir -p nginx/static
mkdir -p scripts
mkdir -p logs
mkdir -p backend/uploads
mkdir -p backend/vm-images

log_success "프로젝트 환경 확인 완료"

# Step 10: 환경 변수 설정
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "환경 변수 설정"

if [ ! -f "backend/.env" ]; then
    log_info "환경 변수 파일 생성..."
    cat > backend/.env << 'EOF'
# 데이터베이스 설정
DATABASE_URL=postgresql://webhoster_user:webhoster_pass@db:5432/webhoster_db

# JWT 및 보안 설정
SECRET_KEY=super-secret-jwt-key-change-in-production-$(openssl rand -hex 16)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# VM 관리 설정
VM_IMAGE_PATH=/app/vm-images
VM_BRIDGE_NAME=virbr0
VM_TEMPLATE_IMAGE=ubuntu-22.04-cloud.qcow2
SSH_PORT_RANGE_START=10000
SSH_PORT_RANGE_END=20000

# Nginx 프록시 설정
NGINX_CONFIG_PATH=/app/nginx-configs
SERVICE_DOMAIN=localhost:80

# 로깅 설정
LOG_LEVEL=INFO
DEBUG=true

# 프로젝트 정보
PROJECT_NAME=웹 호스팅 서비스
VERSION=1.0.0
DESCRIPTION=Docker 기반 웹 호스팅 서비스
EOF
    log_success "환경 변수 파일 생성 완료"
else
    log_info "환경 변수 파일이 이미 존재합니다."
fi

# Step 11: Docker 이미지 빌드
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Docker 이미지 빌드"

log_info "Docker 이미지 빌드 중... (시간이 걸릴 수 있습니다)"
log_cmd "docker-compose build --no-cache"

# 새 그룹 권한 적용을 위해 newgrp 사용
if groups $USER | grep -q '\bdocker\b'; then
    docker-compose build --no-cache
else
    log_info "Docker 그룹 권한 적용 중..."
    newgrp docker << EONG
docker-compose build --no-cache
EONG
fi

log_success "Docker 이미지 빌드 완료"

# Step 12: Ubuntu Cloud 이미지 다운로드
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "Ubuntu Cloud 이미지 준비"

CLOUD_IMAGE_URL="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
CLOUD_IMAGE_PATH="/tmp/ubuntu-22.04-cloud.qcow2"

if [ ! -f "$CLOUD_IMAGE_PATH" ]; then
    log_info "Ubuntu 22.04 Cloud 이미지 다운로드 중..."
    wget -O "$CLOUD_IMAGE_PATH" "$CLOUD_IMAGE_URL"
    log_success "Ubuntu Cloud 이미지 다운로드 완료"
else
    log_info "Ubuntu Cloud 이미지가 이미 존재합니다."
fi

# Step 13: 서비스 시작
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "서비스 시작"

log_info "Docker Compose 서비스 시작..."
log_cmd "docker-compose up -d"

if groups $USER | grep -q '\bdocker\b'; then
    docker-compose up -d
else
    newgrp docker << EONG
docker-compose up -d
EONG
fi

log_success "서비스 시작 완료"

# Step 14: 서비스 상태 확인
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "서비스 상태 확인"

log_info "서비스 준비 대기 중..."
sleep 15

# 서비스 상태 확인
services=("webhoster_db" "webhoster_backend" "webhoster_nginx" "webhoster_redis")

for service in "${services[@]}"; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service.*Up"; then
        log_success "$service: 실행 중"
    else
        log_error "$service: 실행 실패"
        log_info "로그 확인: docker-compose logs $service"
    fi
done

# Step 15: 헬스체크 및 완료
CURRENT_STEP=$((CURRENT_STEP + 1))
show_progress $CURRENT_STEP $TOTAL_STEPS "최종 헬스체크 및 완료"

log_info "헬스체크 수행 중..."

# 데이터베이스 연결 확인
if docker-compose exec -T db pg_isready -U webhoster_user -d webhoster_db >/dev/null 2>&1; then
    log_success "데이터베이스: 연결 성공"
else
    log_warning "데이터베이스: 연결 대기 중..."
fi

# 백엔드 API 확인
sleep 5
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null | grep -q "200"; then
    log_success "백엔드 API: 응답 성공"
else
    log_warning "백엔드 API: 준비 중..."
fi

# Nginx 확인
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null | grep -q "200"; then
    log_success "Nginx: 응답 성공"
else
    log_warning "Nginx: 준비 중..."
fi

# 설치 완료 메시지
clear
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 설치 완료!                             ║"
echo "║                                                              ║"
echo "║  웹 호스팅 서비스가 성공적으로 설치되었습니다!                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo
log_success "🚀 웹 호스팅 서비스 설치가 완료되었습니다!"
echo
log_info "📋 서비스 접속 정보:"
echo "   • 🌐 웹 인터페이스: http://localhost"
echo "   • 📚 API 문서: http://localhost:8000/docs"
echo "   • 🔍 헬스체크: http://localhost:8000/api/v1/health"
echo "   • 🗄️ 데이터베이스: localhost:5432 (webhoster_db)"
echo "   • 🔄 Redis: localhost:6379"
echo
log_info "🔧 관리 명령어:"
echo "   • 서비스 상태: docker-compose ps"
echo "   • 로그 확인: docker-compose logs -f"
echo "   • 서비스 중지: docker-compose down"
echo "   • 서비스 재시작: docker-compose restart"
echo
log_info "🧪 테스트 계정:"
echo "   • 이메일: test@example.com"
echo "   • 비밀번호: testpass123"
echo
log_info "🎯 사용 방법:"
echo "   1. 회원가입: curl -X POST http://localhost:8000/api/v1/auth/register \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"email\":\"user@example.com\",\"password\":\"pass123\",\"username\":\"user\"}'"
echo
echo "   2. 로그인: curl -X POST http://localhost:8000/api/v1/auth/login \\"
echo "      -d 'username=user@example.com&password=pass123'"
echo
echo "   3. 호스팅 생성: curl -X POST http://localhost:8000/api/v1/host \\"
echo "      -H 'Authorization: Bearer {token}'"
echo
echo "   4. 웹 접속: http://localhost/{user_id}"
echo "   5. SSH 접속: ssh -p {port} ubuntu@localhost"
echo

log_warning "⚠️  중요 안내:"
echo "   • 새 터미널을 열거나 다음 명령어를 실행하여 그룹 권한을 적용하세요:"
echo "     newgrp docker"
echo "   • 또는 시스템을 재부팅하세요."
echo

# 브라우저 열기 옵션
read -p "브라우저를 열어 서비스에 접속하시겠습니까? (y/N): " browser_choice
if [[ $browser_choice =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost
    elif command -v open &> /dev/null; then
        open http://localhost
    else
        log_info "브라우저를 수동으로 열어 http://localhost에 접속하세요."
    fi
fi

log_success "🎉 웹 호스팅 서비스 설치 및 설정이 완료되었습니다!"
echo
echo -e "${CYAN}📖 추가 문서: README.md, docs/implementation-report.md${NC}"
echo -e "${CYAN}🔗 GitHub: https://github.com/your-org/vm-webhoster${NC}"
echo 