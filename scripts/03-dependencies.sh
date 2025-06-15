#!/bin/bash

# 🚀 3단계: 의존성 설치
# Python 가상환경, 백엔드 의존성, 프론트엔드 의존성 설치

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

echo -e "${GREEN}🚀 3단계: 의존성 설치${NC}"
echo "================================================"

# 프로젝트 디렉토리 확인
if [ ! -f "backend/requirements.txt" ] || [ ! -f "frontend/package.json" ]; then
    log_error "프로젝트 디렉토리가 올바르지 않습니다. vm-webhoster 디렉토리에서 실행하세요."
    exit 1
fi

# 백엔드 의존성 설치
log_step "백엔드 Python 가상환경 및 의존성 설치"
cd backend

# 가상환경 생성
if [ ! -d "venv" ]; then
    log_info "Python 가상환경 생성 중..."
    python3 -m venv venv
    log_success "가상환경 생성 완료"
fi

# 가상환경 활성화
log_info "가상환경 활성화..."
source venv/bin/activate

# pip 업그레이드
log_info "pip 업그레이드..."
pip install --upgrade pip

# 의존성 설치
log_info "Python 의존성 설치 중... (시간이 걸릴 수 있습니다)"
pip install -r requirements.txt

# 중요한 모듈들 설치 검증
log_info "중요 모듈 설치 검증 중..."
python -c "import requests; print('✅ requests 모듈:', requests.__version__)" 2>/dev/null || {
    log_warning "requests 모듈이 설치되지 않았습니다. 개별 설치 시도..."
    pip install requests
    python -c "import requests; print('✅ requests 모듈 설치 완료:', requests.__version__)"
}

python -c "import jinja2; print('✅ jinja2 모듈:', jinja2.__version__)" 2>/dev/null || {
    log_error "jinja2 모듈이 설치되지 않았습니다!"
    exit 1
}

python -c "import fastapi; print('✅ fastapi 모듈:', fastapi.__version__)" 2>/dev/null || {
    log_error "fastapi 모듈이 설치되지 않았습니다!"
    exit 1
}

log_success "백엔드 의존성 설치 완료"

# 버전 확인
echo "🔍 설치된 주요 패키지 버전:"
pip show fastapi sqlalchemy alembic psycopg2-binary redis 2>/dev/null | grep -E "Name|Version" | paste - - | sed 's/Name: /  /' | sed 's/Version: / v/'

cd ..

# 프론트엔드 의존성 설치
log_step "프론트엔드 Node.js 의존성 설치"
cd frontend

# Node.js 버전 확인
log_info "Node.js 환경:"
echo "  - Node.js: $(node --version)"
echo "  - npm: $(npm --version)"

# npm 캐시 정리 (선택사항)
log_info "npm 캐시 정리..."
npm cache clean --force

# 의존성 설치
log_info "Node.js 의존성 설치 중... (시간이 걸릴 수 있습니다)"
npm install

# 의존성 보안 감사 (선택사항)
log_info "의존성 보안 검사..."
npm audit --audit-level moderate || log_warning "일부 보안 취약점이 발견되었습니다. 'npm audit fix' 실행을 고려하세요."

log_success "프론트엔드 의존성 설치 완료"

# 설치된 주요 패키지 확인
echo "🔍 설치된 주요 패키지 버전:"
npm list --depth=0 | grep -E "@|next|react|typescript" | head -10

cd ..

# 추가 도구 설치 (전역)
log_step "전역 개발 도구 설치"
sudo npm install -g @vercel/ncc pm2 nodemon

log_success "전역 도구 설치 완료"

# Docker 그룹 권한 확인
log_step "Docker 권한 확인"
if groups $USER | grep -q docker; then
    log_success "Docker 그룹 권한 확인됨"
else
    log_warning "Docker 그룹 권한이 없습니다. 재로그인 후 다시 시도하세요."
    log_info "또는 다음 명령어를 실행하세요: sudo usermod -aG docker $USER && newgrp docker"
fi

# 서비스 상태 확인
log_step "필수 서비스 상태 확인"
echo "📊 서비스 상태:"

# PostgreSQL 확인
if systemctl is-active --quiet postgresql; then
    echo "  ✅ PostgreSQL: 실행 중"
else
    echo "  ❌ PostgreSQL: 중지됨"
    log_warning "PostgreSQL을 시작하세요: sudo systemctl start postgresql"
fi

# Redis 확인
if systemctl is-active --quiet redis-server; then
    echo "  ✅ Redis: 실행 중"
else
    echo "  ❌ Redis: 중지됨"
    log_warning "Redis를 시작하세요: sudo systemctl start redis-server"
fi

# Docker 확인
if systemctl is-active --quiet docker; then
    echo "  ✅ Docker: 실행 중"
else
    echo "  ❌ Docker: 중지됨"
    log_warning "Docker를 시작하세요: sudo systemctl start docker"
fi

echo -e "${GREEN}✅ 3단계: 의존성 설치 완료${NC}"
echo "================================================"
echo "🔍 설치 요약:"
echo "  - Python 가상환경: backend/venv"
echo "  - 백엔드 의존성: 설치됨"
echo "  - 프론트엔드 의존성: 설치됨"
echo "  - 전역 도구: @vercel/ncc, pm2, nodemon"
echo "다음 단계: ./scripts/04-database-init.sh" 