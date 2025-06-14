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

# 데이터베이스 연결 테스트
log_step "데이터베이스 연결 테스트"
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('$DATABASE_URL')
    print('  ✅ 데이터베이스 연결 성공')
    conn.close()
except Exception as e:
    print(f'  ❌ 데이터베이스 연결 실패: {e}')
    exit(1)
" || {
    log_error "데이터베이스 연결 실패. PostgreSQL 서비스와 설정을 확인하세요."
    exit 1
}

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