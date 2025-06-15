#!/bin/bash

# 🚀 서비스 시작 스크립트 (개선판)
# 백엔드와 프론트엔드 서비스를 실제로 시작합니다

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

echo -e "${GREEN}🚀 서비스 시작 스크립트 (개선판)${NC}"
echo "==============================="

# 프로젝트 루트 확인
if [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    log_error "프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

# 로그 디렉토리 생성
mkdir -p logs

# 기존 프로세스 종료
log_step "기존 서비스 프로세스 정리 중..."

# Node.js 프로세스 종료
pkill -f "next" 2>/dev/null || true
pkill -f "node.*3000" 2>/dev/null || true

# Python 프로세스 종료  
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "python.*8000" 2>/dev/null || true

# PM2 프로세스 정리 (있다면)
which pm2 >/dev/null 2>&1 && pm2 delete all 2>/dev/null || true

log_success "기존 프로세스 정리 완료"

# 환경변수 로딩
log_step "환경변수 로딩..."
if [[ -f "local.env" ]]; then
    export $(grep -v '^#' local.env | xargs)
    log_success "local.env 로딩 완료"
elif [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
    log_success ".env 로딩 완료"
else
    log_warning "환경변수 파일을 찾을 수 없습니다. 기본값 사용"
fi

# 백엔드 서비스 시작
log_step "백엔드 서비스 시작 중..."
cd backend

# 가상환경 활성화
if [[ -d "venv" ]]; then
    source venv/bin/activate
    log_info "Python 가상환경 활성화됨"
else
    log_error "Python 가상환경이 없습니다. ./scripts/fix-dependencies.sh를 먼저 실행하세요."
    exit 1
fi

# 데이터베이스 연결 테스트
log_info "데이터베이스 연결 테스트..."
if python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://webhoster_user:webhoster_pass@localhost:5432/webhoster_db')
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
    log_success "데이터베이스 연결 성공"
else
    log_error "데이터베이스 연결 실패. ./scripts/fix-database.sh를 먼저 실행하세요."
    cd ..
    exit 1
fi

# 백엔드 서버 시작 (백그라운드)
log_info "FastAPI 서버 시작 중... (포트 8000)"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

# 백엔드 시작 대기
log_info "백엔드 서버 시작 대기 중..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "백엔드 서버 시작 완료 (PID: $BACKEND_PID)"
        break
    elif [ $i -eq 30 ]; then
        log_error "백엔드 서버 시작 실패 (타임아웃)"
        log_info "백엔드 로그 확인: tail -f logs/backend.log"
        cd ..
        exit 1
    else
        echo -n "."
        sleep 2
    fi
done

cd ..

# 프론트엔드 서비스 시작
log_step "프론트엔드 서비스 시작 중..."
cd frontend

# Node.js 의존성 확인
if [[ ! -d "node_modules" ]]; then
    log_info "Node.js 의존성 설치 중..."
    npm install
fi

# 환경변수 설정
export NODE_ENV=development
export NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# 프론트엔드 서버 시작 (백그라운드)
log_info "Next.js 서버 시작 중... (포트 3000)"
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# 프론트엔드 시작 대기
log_info "프론트엔드 서버 시작 대기 중..."
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log_success "프론트엔드 서버 시작 완료 (PID: $FRONTEND_PID)"
        break
    elif [ $i -eq 60 ]; then
        log_error "프론트엔드 서버 시작 실패 (타임아웃)"
        log_info "프론트엔드 로그 확인: tail -f logs/frontend.log"
        cd ..
        exit 1
    else
        echo -n "."
        sleep 3
    fi
done

cd ..

# 서비스 상태 확인
log_step "서비스 상태 최종 확인..."

echo ""
echo "📊 실행 중인 서비스:"
echo "  ├─ 백엔드 (PID: $BACKEND_PID): http://localhost:8000"
echo "  ├─ 프론트엔드 (PID: $FRONTEND_PID): http://localhost:3000"
echo "  ├─ API 문서: http://localhost:8000/docs"
echo "  └─ 헬스체크: http://localhost:8000/health"

# 포트 사용 확인
log_info "포트 사용 현황:"
ss -tlnp | grep -E ":3000|:8000" | while read line; do
    echo "  $line"
done

# PID 파일 저장
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
log_success "🎉 모든 서비스가 성공적으로 시작되었습니다!"
echo ""
echo "🌐 접속 정보:"
echo "  📱 프론트엔드: http://localhost:3000"
echo "  📡 백엔드 API: http://localhost:8000"
echo "  📚 API 문서: http://localhost:8000/docs"
echo ""
echo "🛠️  관리 명령어:"
echo "  ├─ 백엔드 로그: tail -f logs/backend.log"
echo "  ├─ 프론트엔드 로그: tail -f logs/frontend.log"
echo "  ├─ 서비스 중지: kill $BACKEND_PID $FRONTEND_PID"
echo "  └─ 전체 중지: ./scripts/stop-all.sh"
echo ""
echo "⏰ 서비스가 완전히 로드되기까지 1-2분 정도 기다려주세요." 