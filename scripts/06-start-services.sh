#!/bin/bash

# 🚀 6단계: 서비스 시작
# 백엔드, 프론트엔드 서비스 시작 및 상태 확인

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

echo -e "${GREEN}🚀 6단계: 서비스 시작${NC}"
echo "================================================"

# 로그 디렉토리 생성
log_step "로그 디렉토리 준비"
mkdir -p logs
log_success "로그 디렉토리 준비 완료"

# 기존 프로세스 정리
log_step "기존 프로세스 정리"
echo "🧹 기존 서비스 프로세스 종료 중..."

# FastAPI/Uvicorn 프로세스 종료
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "fastapi" 2>/dev/null || true

# Next.js 프로세스 종료
pkill -f "next.*dev" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true

# 조금 대기
sleep 3
log_success "기존 프로세스 정리 완료"

# 필수 서비스 상태 확인
log_step "필수 서비스 상태 확인"
echo "📊 인프라 서비스 상태:"

services_ok=true

# PostgreSQL 확인
if systemctl is-active --quiet postgresql; then
    echo "  ✅ PostgreSQL: 실행 중"
else
    echo "  ❌ PostgreSQL: 중지됨"
    log_info "PostgreSQL 시작 중..."
    sudo systemctl start postgresql
    services_ok=false
fi

# Redis 확인
if systemctl is-active --quiet redis-server; then
    echo "  ✅ Redis: 실행 중"
else
    echo "  ❌ Redis: 중지됨"
    log_info "Redis 시작 중..."
    sudo systemctl start redis-server
    services_ok=false
fi

# Docker 확인
if systemctl is-active --quiet docker; then
    echo "  ✅ Docker: 실행 중"
else
    echo "  ❌ Docker: 중지됨"
    log_info "Docker 시작 중..."
    sudo systemctl start docker
    services_ok=false
fi

# Nginx 확인
if systemctl is-active --quiet nginx; then
    echo "  ✅ Nginx: 실행 중"
else
    echo "  ❌ Nginx: 중지됨"
    log_info "Nginx 시작 중..."
    sudo systemctl start nginx
    services_ok=false
fi

if [ "$services_ok" = false ]; then
    log_info "인프라 서비스 시작 완료. 5초 대기..."
    sleep 5
fi

# 백엔드 서비스 시작
log_step "백엔드 서비스 시작"
cd backend

# 가상환경 활성화 확인
if [ ! -f "venv/bin/activate" ]; then
    log_error "Python 가상환경을 찾을 수 없습니다. 3단계를 먼저 실행하세요."
    exit 1
fi

source venv/bin/activate

# 환경변수 로딩
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs) 2>/dev/null || true
    log_success "환경변수 로딩 완료"
else
    log_error ".env 파일을 찾을 수 없습니다."
    exit 1
fi

# 백엔드 의존성 최종 확인
log_info "백엔드 의존성 확인..."
python3 -c "
try:
    import fastapi, sqlalchemy, alembic, psycopg2, redis
    print('  ✅ 주요 의존성 확인됨')
except ImportError as e:
    print(f'  ❌ 의존성 오류: {e}')
    exit(1)
"

# 데이터베이스 연결 테스트
log_info "데이터베이스 연결 테스트..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('$DATABASE_URL')
    conn.close()
    print('  ✅ 데이터베이스 연결 성공')
except Exception as e:
    print(f'  ❌ 데이터베이스 연결 실패: {e}')
    exit(1)
"

# 백엔드 서버 시작
log_info "FastAPI 서버 시작 중..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "  📋 백엔드 PID: $BACKEND_PID"

cd ..

# 백엔드 서비스 상태 확인
log_info "백엔드 서비스 준비 대기..."
for i in {1..30}; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        log_success "백엔드 서비스 준비 완료!"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        log_error "백엔드 서비스 시작 실패. 로그를 확인하세요: tail -f logs/backend.log"
        exit 1
    fi
done

# 프론트엔드 서비스 시작
log_step "프론트엔드 서비스 시작"
cd frontend

# Node.js 의존성 확인
if [ ! -d "node_modules" ]; then
    log_warning "Node.js 의존성이 설치되지 않았습니다. 설치 중..."
    npm install
fi

# 환경변수 확인
if [ ! -f ".env.local" ]; then
    log_warning ".env.local 파일이 없습니다. 기본값으로 생성 중..."
    VM_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://${VM_IP:-localhost}:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://${VM_IP:-localhost}:8000/ws
EOF
fi

# Next.js 개발 서버 시작
log_info "Next.js 개발 서버 시작 중..."
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  📋 프론트엔드 PID: $FRONTEND_PID"

cd ..

# 프론트엔드 서비스 상태 확인
log_info "프론트엔드 서비스 준비 대기..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log_success "프론트엔드 서비스 준비 완료!"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        log_warning "프론트엔드 서비스 시작에 시간이 걸리고 있습니다."
        break
    fi
done

# 서비스 상태 종합 확인
log_step "전체 서비스 상태 확인"
echo "🔍 서비스 상태 점검:"

# 포트 사용 확인
check_service() {
    local port=$1
    local name=$2
    local url=$3
    
    if ss -tlnp | grep -q ":$port "; then
        if [ ! -z "$url" ] && curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
            echo "  ✅ $name (포트 $port): 실행 중 ✓"
        else
            echo "  🟡 $name (포트 $port): 포트 열림, 응답 대기 중"
        fi
    else
        echo "  ❌ $name (포트 $port): 실행되지 않음"
    fi
}

check_service 8000 "백엔드 API" "http://localhost:8000/docs"
check_service 3000 "프론트엔드" "http://localhost:3000"
check_service 80 "Nginx 프록시" "http://localhost:80"
check_service 5432 "PostgreSQL"
check_service 6379 "Redis"

# PID 파일 저장
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

# 네트워크 정보 표시
log_step "접속 정보"
VM_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || echo "감지실패")

echo "🌐 접속 URL:"
echo ""
echo "📍 로컬 접속:"
echo "  - 메인 사이트: http://localhost"
echo "  - 백엔드 API: http://localhost:8000/docs"
echo "  - 프론트엔드: http://localhost:3000"
echo ""

if [ "$VM_IP" != "" ] && [ "$VM_IP" != "감지실패" ]; then
    echo "📍 VM 내부 접속:"
    echo "  - 메인 사이트: http://$VM_IP"
    echo "  - 백엔드 API: http://$VM_IP:8000/docs"
    echo "  - 프론트엔드: http://$VM_IP:3000"
    echo ""
fi

if [ "$EXTERNAL_IP" != "감지실패" ]; then
    echo "📍 외부 접속 (포트포워딩 설정 필요):"
    echo "  - 메인 사이트: http://$EXTERNAL_IP"
    echo "  - 백엔드 API: http://$EXTERNAL_IP:8000/docs"
    echo "  - 프론트엔드: http://$EXTERNAL_IP:3000"
    echo ""
fi

# 관리 명령어 안내
echo "🛠️ 관리 명령어:"
echo "  - 로그 확인: tail -f logs/backend.log logs/frontend.log"
echo "  - 서비스 중지: ./scripts/stop-all.sh"
echo "  - 디버깅: ./scripts/debug-services.sh"
echo "  - 상태 확인: ./scripts/07-test-services.sh"

echo -e "${GREEN}✅ 6단계: 서비스 시작 완료${NC}"
echo "================================================"
echo "🎉 모든 서비스가 실행 중입니다!"
echo "다음 단계: ./scripts/07-test-services.sh" 