#!/bin/bash

# 웹 호스팅 서비스 - Python 가상환경 설정 스크립트

set -e  # 에러 발생 시 스크립트 중단

echo "🐍 Python 가상환경 설정을 시작합니다..."

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")/.."

# Python 3.10+ 버전 확인
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
echo "✅ Python 버전: $python_version"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ Python 3.10 이상이 필요합니다."
    exit 1
fi

# backend 디렉토리로 이동
cd backend

# 기존 가상환경 제거 (있다면)
if [ -d "venv" ]; then
    echo "🗑️  기존 가상환경을 제거합니다..."
    rm -rf venv
fi

# 새 가상환경 생성
echo "📦 새 가상환경을 생성합니다..."
python3 -m venv venv

# 가상환경 활성화
echo "🔧 가상환경을 활성화합니다..."
source venv/bin/activate

# pip 업그레이드
echo "⬆️  pip을 업그레이드합니다..."
pip install --upgrade pip

# requirements.txt에서 패키지 설치
echo "📚 패키지를 설치합니다..."
pip install -r requirements.txt

echo "✅ 가상환경 설정이 완료되었습니다!"
echo ""
echo "가상환경을 활성화하려면:"
echo "  cd backend && source venv/bin/activate"
echo ""
echo "애플리케이션을 실행하려면:"
echo "  python main.py"
echo "  또는"
echo "  uvicorn main:app --reload" 