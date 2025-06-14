#!/bin/bash
echo "🚀 모든 서비스 시작 중..."

# 백엔드 백그라운드 실행
echo "백엔드 서버 시작..."
cd backend
source venv/bin/activate
# 한글 주석을 제외하고 환경변수만 export (= 기호가 있는 라인만 처리)
export $(grep -v '^#' ../local.env | grep '=' | xargs)
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "백엔드 PID: $BACKEND_PID"
cd ..

# 잠시 대기
sleep 3

# 프론트엔드 실행
echo "프론트엔드 서버 시작..."
cd frontend
npm run dev -- --port 3000
