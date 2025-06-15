#!/bin/bash

# 🔧 의존성 문제 해결 스크립트
# Redis 및 기타 누락된 의존성을 설치합니다

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

echo -e "${GREEN}🔧 의존성 문제 해결 스크립트${NC}"
echo "===================================="

# 현재 디렉토리 확인
if [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    log_error "프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

# 백엔드 의존성 재설치
log_info "백엔드 Python 의존성 재설치 중..."
cd backend

# 가상환경 활성화
if [[ -d "venv" ]]; then
    source venv/bin/activate
    log_info "기존 가상환경 활성화됨"
else
    log_info "새로운 가상환경 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
fi

# pip 업그레이드
log_info "pip 업그레이드..."
pip install --upgrade pip

# requirements.txt 재설치
log_info "Python 패키지 재설치 중..."
pip install -r requirements.txt --force-reinstall

log_success "백엔드 의존성 재설치 완료"

# Redis 연결 테스트
log_info "Redis 연결 테스트..."
if python3 -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('Redis 연결 성공')" 2>/dev/null; then
    log_success "Redis 연결 테스트 통과"
else
    log_warning "Redis 연결 실패. Redis 서비스를 시작하세요: sudo systemctl start redis-server"
fi

# PostgreSQL 연결 테스트
log_info "PostgreSQL 연결 테스트..."
if python3 -c "import psycopg2; conn = psycopg2.connect('postgresql://webhoster_user:webhoster_pass@localhost:5432/webhoster_db'); conn.close(); print('PostgreSQL 연결 성공')" 2>/dev/null; then
    log_success "PostgreSQL 연결 테스트 통과"
else
    log_warning "PostgreSQL 연결 실패. 데이터베이스와 사용자를 생성하세요."
fi

cd ..

# 프론트엔드 의존성 확인
log_info "프론트엔드 의존성 확인 중..."
cd frontend

if [[ -f "package.json" ]]; then
    log_info "npm 의존성 재설치..."
    npm install --force
    log_success "프론트엔드 의존성 재설치 완료"
fi

cd ..

log_success "모든 의존성 문제 해결 완료!"
echo ""
echo "🎯 다음 단계:"
echo "  1. ./scripts/04-database-init.sh 실행"
echo "  2. ./scripts/06-start-services.sh 실행"
echo "  3. ./scripts/07-test-services.sh 실행"
