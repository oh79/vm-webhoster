#!/bin/bash
echo "�� 프론트엔드 서버 시작 중..."

# 디렉토리 이동
cd frontend || {
    echo "❌ 프론트엔드 디렉토리로 이동 실패"
    exit 1
}

# package.json 확인
if [ ! -f "package.json" ]; then
    echo "❌ package.json 파일을 찾을 수 없습니다"
    exit 1
fi

# node_modules 확인
if [ ! -d "node_modules" ]; then
    echo "📦 의존성 설치 중..."
    npm install
fi

echo "✅ 프론트엔드 환경 확인 완료"
echo "🔄 프론트엔드 서버 시작 중..."
npm run dev
