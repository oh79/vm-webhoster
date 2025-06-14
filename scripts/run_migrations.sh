#!/bin/bash

# 웹 호스팅 서비스 - 데이터베이스 마이그레이션 스크립트

set -e  # 에러 발생 시 스크립트 중단

echo "🗄️  데이터베이스 마이그레이션을 시작합니다..."

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")/.."

# backend 디렉토리로 이동
cd backend

# 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "🔧 가상환경을 활성화합니다..."
    source venv/bin/activate
fi

# 환경변수 설정
if [ -f ".env" ]; then
    echo "📋 .env 파일에서 환경변수를 로드합니다..."
    # 중요한 환경변수만 로드
    if grep -q "^DATABASE_URL=" .env; then
        export DATABASE_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
    fi
    if grep -q "^SECRET_KEY=" .env; then
        export SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d'=' -f2-)
    fi
    if grep -q "^DEBUG=" .env; then
        export DEBUG=$(grep "^DEBUG=" .env | cut -d'=' -f2-)
    fi
else
    echo "⚠️  .env 파일이 없습니다. SQLite를 사용합니다..."
    export DATABASE_URL="sqlite:///./webhoster_dev.db"
fi

echo "🔗 데이터베이스 URL: $DATABASE_URL"

# 마이그레이션 상태 확인
echo "📊 현재 마이그레이션 상태를 확인합니다..."
alembic current

# 마이그레이션 실행
echo "⬆️  마이그레이션을 실행합니다..."
alembic upgrade head

echo "✅ 마이그레이션이 완료되었습니다!"

# 마이그레이션 이력 확인
echo "📜 마이그레이션 이력:"
alembic history --verbose 