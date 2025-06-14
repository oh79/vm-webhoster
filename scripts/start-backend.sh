#!/bin/bash
echo "🚀 백엔드 서버 시작 중..."
cd backend
source venv/bin/activate
# 한글 주석을 제외하고 환경변수만 export
export $(grep -v '^#' .env | grep '=' | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
