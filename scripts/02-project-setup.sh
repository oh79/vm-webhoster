#!/bin/bash

# 🚀 2단계: 프로젝트 다운로드 및 기본 설정
# Git 클론, 환경변수 설정, 데이터베이스 준비

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

echo -e "${GREEN}🚀 2단계: 프로젝트 다운로드 및 기본 설정${NC}"
echo "================================================"

# 프로젝트 클론 (이미 있다면 업데이트)
log_step "프로젝트 소스코드 준비"
if [ -d "vm-webhoster" ]; then
    log_info "기존 프로젝트 디렉토리 발견. 업데이트 중..."
    cd vm-webhoster
    git pull origin main || git pull origin master || log_warning "Git pull 실패, 기존 코드 사용"
    cd ..
else
    log_info "프로젝트 클론 중... (GitHub에서)"
    # 실제 GitHub 저장소 URL로 변경하세요
    git clone https://github.com/your-username/vm-webhoster.git || {
        log_error "Git 클론 실패. 수동으로 프로젝트를 다운로드하세요."
        log_info "대안: 프로젝트 zip 파일을 다운로드하고 압축 해제"
        exit 1
    }
fi

cd vm-webhoster
log_success "프로젝트 소스코드 준비 완료"

# 디렉토리 구조 확인
log_step "프로젝트 구조 확인"
tree -L 2 -I 'node_modules|venv|__pycache__|.git' || ls -la

# 환경변수 설정
log_step "환경변수 파일 설정"
if [ ! -f "backend/.env" ]; then
    if [ -f "local.env" ]; then
        cp local.env backend/.env
        log_success "local.env를 backend/.env로 복사 완료"
    else
        log_info "기본 환경변수 파일 생성 중..."
        cat > backend/.env << 'EOF'
# 데이터베이스 설정
DATABASE_URL=postgresql://webhoster_user:webhoster_pass@localhost:5432/webhoster_db

# JWT 인증 설정
SECRET_KEY=super-secret-jwt-key-change-in-production-12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Redis 설정
REDIS_URL=redis://localhost:6379/0

# VM 관리 설정
VM_BRIDGE_NAME=virbr0
VM_IMAGE_PATH=./vm-images
SSH_PORT_RANGE_START=10022
SSH_PORT_RANGE_END=10100
HTTP_PORT_RANGE_START=8080
HTTP_PORT_RANGE_END=8180

# CORS 설정
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# 개발 설정
DEBUG=true
LOG_LEVEL=INFO
RELOAD=true
EOF
        log_success "기본 환경변수 파일 생성 완료"
    fi
else
    log_info "기존 .env 파일 사용"
fi

# VM의 IP 주소 자동 감지 및 설정
log_step "VM IP 주소 자동 설정"
VM_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
if [ ! -z "$VM_IP" ]; then
    log_info "감지된 VM IP: $VM_IP"
    
    # 프론트엔드 환경변수 설정
    cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://$VM_IP:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://$VM_IP:8000/ws
EOF
    
    # 백엔드 환경변수에 CORS 추가
    sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=[\"http://localhost:3000\", \"http://127.0.0.1:3000\", \"http://$VM_IP:3000\"]|" backend/.env
    
    log_success "IP 주소 기반 환경변수 설정 완료"
else
    log_warning "VM IP 자동 감지 실패. 수동 설정이 필요할 수 있습니다."
fi

# 필수 디렉토리 생성
log_step "필수 디렉토리 생성"
mkdir -p backend/vm-images
mkdir -p backend/nginx-configs
mkdir -p logs
mkdir -p uploads

log_success "필수 디렉토리 생성 완료"

# 데이터베이스 설정
log_step "데이터베이스 사용자 및 데이터베이스 생성"
sudo -u postgres psql << 'EOF' || log_warning "데이터베이스 설정 중 일부 오류 (기존 설정이 있을 수 있음)"
CREATE DATABASE webhoster_db;
CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';
GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;
ALTER USER webhoster_user CREATEDB;
\q
EOF

log_success "데이터베이스 설정 완료"

# 권한 설정
log_step "스크립트 실행 권한 설정"
chmod +x scripts/*.sh

log_success "스크립트 권한 설정 완료"

echo -e "${GREEN}✅ 2단계: 프로젝트 다운로드 및 기본 설정 완료${NC}"
echo "================================================"
echo "🔍 설정 확인:"
echo "  - 프로젝트 디렉토리: $(pwd)"
echo "  - VM IP: ${VM_IP:-'자동 감지 실패'}"
echo "  - 데이터베이스: webhoster_db"
echo "다음 단계: ./scripts/03-dependencies.sh" 