#!/bin/bash
echo "🛑 모든 서비스 중지 중..."

# 백엔드 프로세스 종료
pkill -f "uvicorn app.main:app"

# 프론트엔드 프로세스 종료
pkill -f "next-server"

echo "모든 서비스가 중지되었습니다."
