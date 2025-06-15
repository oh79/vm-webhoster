#!/bin/bash

# 🗄️ 데이터베이스 문제 해결 스크립트
# PostgreSQL 사용자와 데이터베이스를 생성합니다

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

echo -e "${GREEN}🗄️ 데이터베이스 문제 해결 스크립트${NC}"
echo "====================================="

# PostgreSQL 서비스 확인
log_info "PostgreSQL 서비스 상태 확인..."
if ! systemctl is-active --quiet postgresql; then
    log_info "PostgreSQL 서비스 시작 중..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# 데이터베이스 사용자 및 DB 생성
log_info "PostgreSQL 사용자 및 데이터베이스 생성 중..."

# postgres 사용자로 실행
sudo -u postgres psql << 'EOF'
-- 기존 사용자와 데이터베이스 삭제 (있다면)
DROP DATABASE IF EXISTS webhoster_db;
DROP USER IF EXISTS webhoster_user;

-- 새 사용자 생성
CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';

-- 새 데이터베이스 생성
CREATE DATABASE webhoster_db OWNER webhoster_user;

-- 사용자에게 권한 부여
GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;

-- 연결 확인
\c webhoster_db

-- 스키마 권한 부여
GRANT ALL ON SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO webhoster_user;

-- 기본 테이블 소유권 변경
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO webhoster_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO webhoster_user;

-- 사용자 정보 확인
\du webhoster_user

-- 데이터베이스 정보 확인
\l webhoster_db

-- 연결 테스트
SELECT 'PostgreSQL 설정 완료!' as message;
EOF

if [ $? -eq 0 ]; then
    log_success "PostgreSQL 사용자 및 데이터베이스 생성 완료"
else
    log_error "PostgreSQL 설정 실패"
    exit 1
fi

# 연결 테스트
log_info "연결 테스트 수행 중..."
if PGPASSWORD=webhoster_pass psql -h localhost -U webhoster_user -d webhoster_db -c "SELECT version();" > /dev/null 2>&1; then
    log_success "데이터베이스 연결 테스트 성공!"
else
    log_error "데이터베이스 연결 테스트 실패"
    exit 1
fi

# pg_hba.conf 설정 확인 및 수정
log_info "PostgreSQL 인증 설정 확인 중..."
PG_HBA_FILE=$(sudo -u postgres psql -t -c "SHOW hba_file;" | xargs)

log_info "pg_hba.conf 파일 위치: $PG_HBA_FILE"

# 로컬 연결에 대한 설정 확인
if ! sudo grep -q "local.*webhoster_db.*webhoster_user.*md5" "$PG_HBA_FILE"; then
    log_info "pg_hba.conf에 로컬 연결 설정 추가 중..."
    
    # 백업 생성
    sudo cp "$PG_HBA_FILE" "$PG_HBA_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    
    # 임시 파일에 설정 작성
    cat > /tmp/webhoster_hba_insert << 'HBAEOF'
# Webhoster application access
local   webhoster_db    webhoster_user                    md5
host    webhoster_db    webhoster_user    127.0.0.1/32    md5

HBAEOF
    
    # 기존 파일 앞에 새 설정 추가
    sudo cat /tmp/webhoster_hba_insert "$PG_HBA_FILE" > /tmp/new_hba.conf
    sudo mv /tmp/new_hba.conf "$PG_HBA_FILE"
    sudo chown postgres:postgres "$PG_HBA_FILE"
    sudo chmod 640 "$PG_HBA_FILE"
    
    # 임시 파일 정리
    rm -f /tmp/webhoster_hba_insert
    
    # PostgreSQL 재시작
    log_info "PostgreSQL 재시작 중..."
    sudo systemctl restart postgresql
    
    # 잠시 대기
    sleep 3
    
    log_success "PostgreSQL 인증 설정 업데이트 완료"
else
    log_info "PostgreSQL 인증 설정이 이미 올바르게 구성되어 있습니다."
fi

# 최종 연결 테스트
log_info "최종 연결 테스트 수행 중..."
if PGPASSWORD=webhoster_pass psql -h localhost -U webhoster_user -d webhoster_db -c "SELECT 'Connection successful!' as result;" 2>/dev/null; then
    log_success "✅ 데이터베이스 설정이 완전히 완료되었습니다!"
else
    log_error "❌ 최종 연결 테스트 실패"
    
    # 디버깅 정보 제공
    log_info "디버깅 정보:"
    echo "  - PostgreSQL 상태: $(systemctl is-active postgresql)"
    echo "  - PostgreSQL 포트: $(sudo -u postgres psql -t -c 'SHOW port;' | xargs)"
    echo "  - 사용 가능한 데이터베이스:"
    sudo -u postgres psql -l
    
    exit 1
fi

echo ""
echo "🎯 다음 단계:"
echo "  1. ./scripts/04-database-init.sh 실행 (마이그레이션)"
echo "  2. ./scripts/06-start-services.sh 실행 (서비스 시작)"
echo "  3. ./scripts/07-test-services.sh 실행 (테스트)" 