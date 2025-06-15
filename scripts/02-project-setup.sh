#!/bin/bash

# 🚀 2단계: 프로젝트 설정 및 환경변수 구성
# 환경변수 설정, 데이터베이스 준비, 기본 설정

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

echo -e "${GREEN}🚀 2단계: 프로젝트 설정 및 환경변수 구성${NC}"
echo "================================================"

# 현재 디렉토리 확인
if [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    log_error "backend 또는 frontend 디렉토리를 찾을 수 없습니다."
    log_error "vm-webhoster 프로젝트 루트 디렉토리에서 실행하세요."
    exit 1
fi

# 프로젝트 구조 확인
log_step "프로젝트 구조 확인"
tree -L 2 -I 'node_modules|venv|__pycache__|.git' 2>/dev/null || ls -la

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
VM_IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7}' | head -1 || echo "")
if [ ! -z "$VM_IP" ]; then
    log_info "감지된 VM IP: $VM_IP"
    
    # 프론트엔드 환경변수 설정
    cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://$VM_IP:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://$VM_IP:8000/ws
EOF
    
    # 백엔드 환경변수에 CORS 추가 (더 안전한 방식)
    if grep -q "CORS_ORIGINS=" backend/.env; then
        sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=[\"http://localhost:3000\", \"http://127.0.0.1:3000\", \"http://$VM_IP:3000\"]|" backend/.env
    else
        echo "CORS_ORIGINS=[\"http://localhost:3000\", \"http://127.0.0.1:3000\", \"http://$VM_IP:3000\"]" >> backend/.env
    fi
    
    log_success "IP 주소 기반 환경변수 설정 완료"
else
    log_warning "VM IP 자동 감지 실패. 기본 설정을 사용합니다."
fi

# 필수 디렉토리 생성
log_step "필수 디렉토리 생성"
mkdir -p backend/vm-images
mkdir -p backend/nginx-configs
mkdir -p logs
mkdir -p uploads
mkdir -p backend/vm-images/containers

log_success "필수 디렉토리 생성 완료"

# PostgreSQL 서비스 상태 확인 및 시작
log_step "PostgreSQL 서비스 확인"
if ! systemctl is-active --quiet postgresql; then
    log_info "PostgreSQL 서비스 시작 중..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    sleep 3
fi

if systemctl is-active --quiet postgresql; then
    log_success "PostgreSQL 서비스 실행 중"
else
    log_error "PostgreSQL 서비스 시작 실패"
    exit 1
fi

# 데이터베이스 설정 (개선된 버전)
log_step "데이터베이스 사용자 및 데이터베이스 생성"

# 기존 설정 정리 및 재생성 (더 안전한 방식)
sudo -u postgres psql << 'EOF' 2>/dev/null || {
    log_warning "데이터베이스 설정 중 일부 오류 발생. 재시도 중..."
}
\set ON_ERROR_STOP off

-- 기존 연결 종료
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'webhoster_db' AND pid <> pg_backend_pid();

-- 기존 데이터베이스와 사용자 삭제 (있다면)
DROP DATABASE IF EXISTS webhoster_db;
DROP USER IF EXISTS webhoster_user;

-- 새로 생성
CREATE DATABASE webhoster_db;
CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';
GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;
ALTER USER webhoster_user CREATEDB;
ALTER DATABASE webhoster_db OWNER TO webhoster_user;

-- 추가 권한 설정
\c webhoster_db
GRANT ALL ON SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO webhoster_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO webhoster_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO webhoster_user;

\q
EOF

# 데이터베이스 연결 테스트
log_step "데이터베이스 연결 테스트"
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw webhoster_db; then
    log_success "데이터베이스 생성 확인됨"
    
    # 실제 연결 테스트
    if PGPASSWORD='webhoster_pass' psql -h localhost -U webhoster_user -d webhoster_db -c '\l' >/dev/null 2>&1; then
        log_success "데이터베이스 연결 테스트 성공"
    else
        log_error "데이터베이스 연결 테스트 실패"
        exit 1
    fi
else
    log_error "데이터베이스 생성 실패"
    exit 1
fi

# 권한 설정
log_step "스크립트 실행 권한 설정"
find scripts/ -name "*.sh" -exec chmod +x {} \; 2>/dev/null || chmod +x scripts/*.sh

log_success "스크립트 권한 설정 완료"

# 추가 설정 파일들 체크
log_step "설정 파일 무결성 검사"
config_files=("backend/.env" "frontend/package.json" "backend/requirements.txt")
all_present=true

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        log_info "✅ $file 존재"
    else
        log_warning "❌ $file 누락"
        all_present=false
    fi
done

if $all_present; then
    log_success "모든 필수 설정 파일 확인됨"
else
    log_warning "일부 설정 파일이 누락되었습니다. 다음 단계에서 문제가 발생할 수 있습니다."
fi

echo -e "${GREEN}✅ 2단계: 프로젝트 설정 및 환경변수 구성 완료${NC}"
echo "================================================"
echo "🔍 설정 확인:"
echo "  - 프로젝트 디렉토리: $(pwd)"
echo "  - VM IP: ${VM_IP:-'자동 감지 실패'}"
echo "  - 데이터베이스: webhoster_db"
echo "  - 데이터베이스 사용자: webhoster_user"
echo "  - 환경변수: backend/.env 생성됨"
echo "다음 단계: ./scripts/03-dependencies.sh" 