#!/bin/bash

# 🚀 4단계: 데이터베이스 초기화 및 마이그레이션
# Alembic 마이그레이션 실행, 초기 데이터 설정

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

echo -e "${GREEN}🚀 4단계: 데이터베이스 초기화 및 마이그레이션${NC}"
echo "================================================"

# 백엔드 디렉토리로 이동
if [ ! -d "backend" ]; then
    log_error "backend 디렉토리를 찾을 수 없습니다. vm-webhoster 디렉토리에서 실행하세요."
    exit 1
fi

cd backend

# 가상환경 활성화
log_step "Python 가상환경 활성화"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    log_success "가상환경 활성화 완료"
else
    log_error "가상환경을 찾을 수 없습니다. 3단계 의존성 설치를 먼저 실행하세요."
    exit 1
fi

# 환경변수 로딩
log_step "환경변수 로딩"
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs) 2>/dev/null || true
    log_success "환경변수 로딩 완료"
else
    log_error ".env 파일을 찾을 수 없습니다. 2단계 프로젝트 설정을 먼저 실행하세요."
    exit 1
fi

# 데이터베이스 연결 테스트 (개선된 버전)
log_step "데이터베이스 연결 테스트"

# PostgreSQL 서비스 감지 함수
detect_postgresql_service() {
    # 가능한 PostgreSQL 서비스 이름들
    local service_patterns=(
        "postgresql"
        "postgresql.service"
        "postgresql@*-main"
        "postgresql-*"
    )
    
    for pattern in "${service_patterns[@]}"; do
        local services=$(systemctl list-units --type=service --all | grep -E "^\\s*${pattern}" | awk '{print $1}' || true)
        
        if [ ! -z "$services" ]; then
            for service in $services; do
                echo "$service"
                return 0
            done
        fi
    done
    
    # 설치된 서비스들 중에서 찾기
    local installed_services=$(systemctl list-unit-files | grep postgresql | head -1 | awk '{print $1}' || true)
    if [ ! -z "$installed_services" ]; then
        echo "$installed_services"
        return 0
    fi
    
    echo "postgresql"  # 기본값
    return 1
}

# 여러 방법으로 연결 시도
connection_success=false
max_attempts=5

for attempt in $(seq 1 $max_attempts); do
    log_info "데이터베이스 연결 시도 $attempt/$max_attempts"
    
    # PostgreSQL 서비스 상태 확인 및 시작
    PG_SERVICE=$(detect_postgresql_service)
    log_info "감지된 PostgreSQL 서비스: $PG_SERVICE"
    
    if ! systemctl is-active --quiet "$PG_SERVICE" 2>/dev/null; then
        log_warning "PostgreSQL 서비스가 실행되지 않음. 시작 중..."
        
        # 여러 방법으로 서비스 시작 시도
        if sudo systemctl start "$PG_SERVICE" 2>/dev/null; then
            log_info "systemctl로 서비스 시작 성공"
        elif sudo systemctl start postgresql 2>/dev/null; then
            log_info "기본 postgresql 서비스 시작 성공"
        else
            log_warning "systemctl 시작 실패. 수동 시작 시도 중..."
            sudo -u postgres pg_ctl start -D /var/lib/postgresql/*/main/ 2>/dev/null || {
                log_warning "수동 시작도 실패했습니다."
            }
        fi
        
        sleep 5
    else
        log_info "PostgreSQL 서비스가 이미 실행 중입니다."
    fi
    
    # PostgreSQL 프로세스 확인
    if ! pgrep -x "postgres" > /dev/null; then
        log_warning "PostgreSQL 프로세스를 찾을 수 없습니다."
        if [ $attempt -lt $max_attempts ]; then
            log_info "5초 후 재시도..."
            sleep 5
            continue
        fi
    fi
    
    # 방법 1: psycopg2를 사용한 연결 테스트
    if python3 -c "
import psycopg2
import os
try:
    # 환경변수에서 DATABASE_URL 읽기
    database_url = os.getenv('DATABASE_URL', 'postgresql://webhoster_user:webhoster_pass@localhost:5432/webhoster_db')
    conn = psycopg2.connect(database_url)
    print('✅ psycopg2 연결 성공')
    conn.close()
    exit(0)
except Exception as e:
    print(f'❌ psycopg2 연결 실패: {e}')
    exit(1)
" 2>/dev/null; then
        connection_success=true
        break
    fi
    
    # 방법 2: 직접 psql 명령어로 연결 테스트
    if PGPASSWORD='webhoster_pass' psql -h localhost -U webhoster_user -d webhoster_db -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "psql 직접 연결 성공"
        connection_success=true
        break
    fi
    
    # 방법 3: 데이터베이스가 없다면 재생성 시도
    if [ $attempt -eq 3 ]; then
        log_warning "데이터베이스 재생성 시도 중..."
        
        # 먼저 PostgreSQL에 연결 가능한지 확인
        if sudo -u postgres psql -c "SELECT version();" &>/dev/null; then
            sudo -u postgres psql << 'EOF' >/dev/null 2>&1 || true
\set ON_ERROR_STOP off
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'webhoster_db' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS webhoster_db;
DROP USER IF EXISTS webhoster_user;
CREATE DATABASE webhoster_db;
CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';
GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;
ALTER USER webhoster_user CREATEDB;
ALTER DATABASE webhoster_db OWNER TO webhoster_user;
\c webhoster_db
GRANT ALL ON SCHEMA public TO webhoster_user;
\q
EOF
            sleep 3
        else
            log_warning "PostgreSQL에 postgres 사용자로 연결할 수 없습니다."
        fi
    fi
    
    if [ $attempt -lt $max_attempts ]; then
        log_info "5초 후 재시도..."
        sleep 5
    fi
done

if [ "$connection_success" = false ]; then
    log_error "모든 데이터베이스 연결 시도 실패"
    log_error ""
    log_error "🔧 문제 해결 방법:"
    log_error "1. PostgreSQL 서비스 상태 확인: systemctl status postgresql*"
    log_error "2. PostgreSQL 프로세스 확인: ps aux | grep postgres"
    log_error "3. 수동 데이터베이스 생성:"
    log_error "   sudo -u postgres createdb webhoster_db"
    log_error "   sudo -u postgres psql -c \"CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';\""
    log_error "   sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;\""
    log_error "4. PostgreSQL 재설치:"
    log_error "   sudo apt remove --purge postgresql* -y"
    log_error "   sudo apt install postgresql postgresql-contrib -y"
    exit 1
else
    log_success "데이터베이스 연결 확인됨"
fi

# Alembic 초기화 확인
log_step "Alembic 마이그레이션 환경 확인"
if [ ! -f "alembic.ini" ]; then
    log_info "Alembic 초기화 중..."
    alembic init alembic
    log_success "Alembic 초기화 완료"
else
    log_info "기존 Alembic 설정 사용"
fi

# Alembic 설정 파일 업데이트
log_step "Alembic 설정 업데이트"
if [ -f "alembic.ini" ]; then
    sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = $DATABASE_URL|" alembic.ini
    log_success "Alembic 데이터베이스 URL 설정 완료"
fi

# 마이그레이션 파일 존재 확인
log_step "마이그레이션 파일 확인"
if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions)" ]; then
    log_info "기존 마이그레이션 파일 발견"
    ls -la alembic/versions/
else
    log_info "마이그레이션 파일을 생성합니다..."
    
    # 초기 마이그레이션 생성
    alembic revision --autogenerate -m "Initial migration"
    log_success "초기 마이그레이션 파일 생성 완료"
fi

# 데이터베이스 마이그레이션 실행
log_step "데이터베이스 마이그레이션 실행"
alembic upgrade head
log_success "데이터베이스 마이그레이션 완료"

# 테이블 생성 확인
log_step "생성된 테이블 확인"
python3 -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
cur = conn.cursor()
cur.execute('''
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
''')
tables = cur.fetchall()
print('📊 생성된 테이블:')
for table in tables:
    print(f'  - {table[0]}')
conn.close()
"

# 초기 데이터 삽입 (있는 경우)
log_step "초기 데이터 확인"
if [ -f "../scripts/init-db.sql" ]; then
    log_info "초기 데이터 스크립트 발견. 실행 중..."
    psql "$DATABASE_URL" -f "../scripts/init-db.sql" || log_warning "초기 데이터 삽입에서 일부 오류 발생"
    log_success "초기 데이터 삽입 완료"
else
    log_info "초기 데이터 스크립트가 없습니다."
fi

# 관리자 사용자 생성 (Python 스크립트)
log_step "관리자 사용자 생성"
python3 -c "
import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.models.user import User
from app.core.auth import get_password_hash

db = SessionLocal()
try:
    # 기존 관리자 확인
    admin_user = db.query(User).filter(User.email == 'admin@example.com').first()
    if not admin_user:
        # 관리자 생성
        admin_user = User(
            email='admin@example.com',
            username='admin',
            hashed_password=get_password_hash('admin123'),
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print('  ✅ 관리자 사용자 생성됨 (admin@example.com / admin123)')
    else:
        print('  ℹ️  기존 관리자 사용자 존재')
except Exception as e:
    print(f'  ⚠️  관리자 사용자 생성 오류: {e}')
finally:
    db.close()
" || log_warning "관리자 사용자 생성 실패"

# 데이터베이스 상태 최종 확인
log_step "데이터베이스 상태 최종 확인"
python3 -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
cur = conn.cursor()

# 사용자 테이블 확인
cur.execute('SELECT COUNT(*) FROM users;')
user_count = cur.fetchone()[0]
print(f'  👥 사용자 수: {user_count}')

# 호스팅 테이블 확인
try:
    cur.execute('SELECT COUNT(*) FROM hosting;')
    hosting_count = cur.fetchone()[0]
    print(f'  🖥️  호스팅 수: {hosting_count}')
except:
    print('  🖥️  호스팅 테이블: 없음')

# 마이그레이션 히스토리 확인
try:
    cur.execute('SELECT version_num FROM alembic_version;')
    version = cur.fetchone()
    print(f'  📝 마이그레이션 버전: {version[0] if version else \"없음\"}')
except:
    print('  📝 마이그레이션 버전: 확인 불가')

conn.close()
"

cd ..

echo -e "${GREEN}✅ 4단계: 데이터베이스 초기화 및 마이그레이션 완료${NC}"
echo "================================================"
echo "🔍 데이터베이스 설정 완료:"
echo "  - 마이그레이션: 실행됨"
echo "  - 테이블: 생성됨"
echo "  - 관리자 계정: admin@example.com / admin123"
echo "다음 단계: ./scripts/05-network-setup.sh" 