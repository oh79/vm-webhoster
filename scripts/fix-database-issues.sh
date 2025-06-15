#!/bin/bash

# 🔧 데이터베이스 문제 해결 스크립트
# PostgreSQL 데이터베이스 및 사용자 설정 문제 해결

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

echo -e "${GREEN}🔧 데이터베이스 문제 해결 스크립트${NC}"
echo "================================================"

# PostgreSQL 서비스 상태 확인 및 재시작
log_step "PostgreSQL 서비스 상태 확인"
if systemctl is-active --quiet postgresql; then
    log_info "PostgreSQL 서비스 실행 중"
else
    log_warning "PostgreSQL 서비스 중지됨. 시작 중..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    sleep 5
fi

if systemctl is-active --quiet postgresql; then
    log_success "PostgreSQL 서비스 정상 실행"
else
    log_error "PostgreSQL 서비스 시작 실패"
    exit 1
fi

# 기존 데이터베이스 연결 강제 종료
log_step "기존 데이터베이스 연결 정리"
sudo -u postgres psql << 'EOF' >/dev/null 2>&1 || true
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'webhoster_db' 
AND pid <> pg_backend_pid();
EOF

# 데이터베이스 및 사용자 완전 재생성
log_step "데이터베이스 및 사용자 완전 재생성"
sudo -u postgres psql << 'EOF'
\set ON_ERROR_STOP off

-- 기존 데이터베이스와 사용자 삭제
DROP DATABASE IF EXISTS webhoster_db;
DROP USER IF EXISTS webhoster_user;

-- 새로운 사용자 생성
CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';
ALTER USER webhoster_user CREATEDB;
ALTER USER webhoster_user CREATEROLE;

-- 새로운 데이터베이스 생성
CREATE DATABASE webhoster_db OWNER webhoster_user;

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;

\q
EOF

# 데이터베이스별 권한 설정
log_step "데이터베이스별 상세 권한 설정"
sudo -u postgres psql -d webhoster_db << 'EOF'
-- public 스키마 권한 부여
GRANT ALL ON SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO webhoster_user;

-- 기본 권한 설정 (새로 생성되는 객체에 대해)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO webhoster_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO webhoster_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO webhoster_user;

\q
EOF

# 연결 테스트
log_step "데이터베이스 연결 테스트"
connection_tests_passed=0

# 테스트 1: PostgreSQL 내부 연결 테스트
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw webhoster_db; then
    log_success "✅ 데이터베이스 존재 확인"
    ((connection_tests_passed++))
else
    log_error "❌ 데이터베이스 존재하지 않음"
fi

# 테스트 2: 사용자 권한 테스트
if sudo -u postgres psql -c "\du" | grep -q webhoster_user; then
    log_success "✅ 사용자 존재 확인"
    ((connection_tests_passed++))
else
    log_error "❌ 사용자 존재하지 않음"
fi

# 테스트 3: 실제 연결 테스트
if PGPASSWORD='webhoster_pass' psql -h localhost -U webhoster_user -d webhoster_db -c "SELECT 1;" >/dev/null 2>&1; then
    log_success "✅ 실제 연결 테스트 성공"
    ((connection_tests_passed++))
else
    log_error "❌ 실제 연결 테스트 실패"
fi

# 테스트 4: Python psycopg2 연결 테스트
if python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://webhoster_user:webhoster_pass@localhost:5432/webhoster_db')
    conn.close()
    print('✅ Python psycopg2 연결 성공')
    exit(0)
except Exception as e:
    print(f'❌ Python psycopg2 연결 실패: {e}')
    exit(1)
" 2>/dev/null; then
    ((connection_tests_passed++))
fi

# 결과 출력
echo ""
echo "📊 데이터베이스 테스트 결과: $connection_tests_passed/4 통과"

if [ $connection_tests_passed -eq 4 ]; then
    log_success "모든 데이터베이스 테스트 통과!"
    echo ""
    echo "🔍 데이터베이스 정보:"
    echo "  - 데이터베이스: webhoster_db"
    echo "  - 사용자: webhoster_user"
    echo "  - 비밀번호: webhoster_pass"
    echo "  - 연결 URL: postgresql://webhoster_user:webhoster_pass@localhost:5432/webhoster_db"
    echo ""
    echo "✅ 이제 00-run-all.sh 스크립트를 다시 실행할 수 있습니다."
else
    log_error "일부 데이터베이스 테스트 실패"
    echo ""
    echo "🔧 수동 해결 방법:"
    echo "1. PostgreSQL 서비스 재시작: sudo systemctl restart postgresql"
    echo "2. 수동 데이터베이스 생성:"
    echo "   sudo -u postgres createdb webhoster_db"
    echo "   sudo -u postgres psql -c \"CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';\""
    echo "   sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;\""
    echo "3. 다시 이 스크립트 실행: ./scripts/fix-database-issues.sh"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 데이터베이스 문제 해결 완료${NC}"
echo "================================================" 