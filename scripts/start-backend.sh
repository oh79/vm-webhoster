#!/bin/bash
echo "🚀 백엔드 서버 시작 중..."

# 디렉토리 이동
cd backend || {
    echo "❌ 백엔드 디렉토리로 이동 실패"
    exit 1
}

# 가상환경 활성화
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ 가상환경 활성화 완료"
else
    echo "❌ 가상환경을 찾을 수 없습니다"
    exit 1
fi

# 환경변수 로딩 (더 안전한 방식)
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✅ 환경변수 로딩 완료"
else
    echo "❌ .env 파일을 찾을 수 없습니다"
    exit 1
fi

# 백엔드 서버 시작
echo "🔄 백엔드 서버 시작 중..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
