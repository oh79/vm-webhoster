#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 통합 서비스 시작 (네트워크 설정 포함)${NC}"
echo "================================================"

# 로그 디렉토리 생성
mkdir -p logs

# 네트워크 설정 함수
setup_network() {
    echo -e "\n${BLUE}🌐 네트워크 및 포트포워딩 설정 중...${NC}"
    
    # 1. 방화벽 포트 열기
    echo -e "${YELLOW}🔥 방화벽 포트 설정...${NC}"
    if command -v ufw &> /dev/null; then
        sudo ufw allow 8000/tcp >/dev/null 2>&1
        sudo ufw allow 3000/tcp >/dev/null 2>&1
        echo -e "${GREEN}✅ UFW 포트 8000, 3000 열기 완료${NC}"
    fi
    
    # 2. iptables 직접 설정 (방화벽 백업)
    sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT >/dev/null 2>&1
    sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT >/dev/null 2>&1
    echo -e "${GREEN}✅ iptables 포트 규칙 추가 완료${NC}"
    
    # 3. IP 포워딩 활성화 (필요시)
    if [ "$(sysctl -n net.ipv4.ip_forward 2>/dev/null)" != "1" ]; then
        echo -e "${YELLOW}📡 IP 포워딩 활성화...${NC}"
        echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf >/dev/null 2>&1
        sudo sysctl -p >/dev/null 2>&1
        echo -e "${GREEN}✅ IP 포워딩 활성화 완료${NC}"
    fi
    
    echo -e "${GREEN}✅ 네트워크 설정 완료!${NC}"
}

# 기존 프로세스 정리 함수
cleanup() {
    echo -e "\n${YELLOW}🧹 기존 프로세스 정리 중...${NC}"
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "next.*dev" 2>/dev/null || true
    sleep 2
}

# 서비스 상태 확인 함수
check_service() {
    local url=$1
    local service_name=$2
    local max_retries=30
    local retry=0
    
    echo -e "${YELLOW}🔍 $service_name 상태 확인 중...${NC}"
    
    while [ $retry -lt $max_retries ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name 서비스 준비 완료!${NC}"
            return 0
        fi
        retry=$((retry + 1))
        echo -e "${YELLOW}⏳ $service_name 대기 중... ($retry/$max_retries)${NC}"
        sleep 2
    done
    
    echo -e "${RED}❌ $service_name 서비스 시작 실패${NC}"
    return 1
}

# 포트 접근성 테스트 함수
test_external_access() {
    local port=$1
    local service_name=$2
    
    EXTERNAL_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
    if [ ! -z "$EXTERNAL_IP" ]; then
        echo -e "${YELLOW}🌍 $service_name 외부 접근 테스트 ($EXTERNAL_IP:$port)...${NC}"
        if curl -s --connect-timeout 5 http://$EXTERNAL_IP:$port > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name 외부 접근 가능${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  $service_name 외부 접근 제한됨 (VM 포트포워딩 설정 필요)${NC}"
            return 1
        fi
    fi
}

# 종료 시그널 핸들러
cleanup_on_exit() {
    echo -e "\n${YELLOW}🛑 서비스 종료 중...${NC}"
    cleanup
    echo -e "${GREEN}✅ 모든 서비스가 종료되었습니다${NC}"
    exit 0
}

# 시그널 트랩 설정
trap cleanup_on_exit INT TERM

# 1. 네트워크 설정 먼저 수행
setup_network

# 2. 기존 프로세스 정리
cleanup

# 3. 백엔드 시작
echo -e "\n${BLUE}🔧 백엔드 서버 시작...${NC}"
cd backend || {
    echo -e "${RED}❌ 백엔드 디렉토리로 이동 실패${NC}"
    exit 1
}

# 가상환경 활성화
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ 가상환경 활성화 완료${NC}"
else
    echo -e "${RED}❌ 가상환경을 찾을 수 없습니다${NC}"
    exit 1
fi

# 환경변수 로딩
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo -e "${GREEN}✅ 환경변수 로딩 완료${NC}"
else
    echo -e "${RED}❌ .env 파일을 찾을 수 없습니다${NC}"
    exit 1
fi

# 백엔드 백그라운드 실행
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ 백엔드 PID: $BACKEND_PID${NC}"

cd ..

# 4. 백엔드 서비스 상태 확인
if ! check_service "http://localhost:8000/docs" "백엔드"; then
    echo -e "${RED}❌ 백엔드 서비스 시작 실패. 로그를 확인하세요:${NC}"
    echo -e "${YELLOW}tail -f logs/backend.log${NC}"
    cleanup
    exit 1
fi

# 5. 프론트엔드 시작
echo -e "\n${BLUE}🎨 프론트엔드 서버 시작...${NC}"
cd frontend || {
    echo -e "${RED}❌ 프론트엔드 디렉토리로 이동 실패${NC}"
    cleanup
    exit 1
}

# 의존성 확인
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 의존성 설치 중...${NC}"
    npm install
fi

# 6. 최종 접근성 테스트
echo -e "\n${BLUE}🌍 네트워크 접근성 테스트...${NC}"
EXTERNAL_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)

# 백엔드 외부 접근 테스트
test_external_access 8000 "백엔드"

echo -e "\n${GREEN}✅ 모든 서비스가 준비되었습니다!${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}📋 접속 정보:${NC}"
echo -e "${YELLOW}로컬 접속:${NC}"
echo -e "  백엔드: http://localhost:8000/docs"
echo -e "  프론트엔드: http://localhost:3000"

if [ ! -z "$EXTERNAL_IP" ]; then
    echo -e "${YELLOW}외부 접속 (VM IP):${NC}"
    echo -e "  백엔드: http://$EXTERNAL_IP:8000/docs"
    echo -e "  프론트엔드: http://$EXTERNAL_IP:3000"
fi

echo -e "${BLUE}📝 관리 명령어:${NC}"
echo -e "  로그 확인: tail -f logs/backend.log"
echo -e "  디버깅: ./scripts/debug-services.sh"
echo -e "  종료: Ctrl+C"

echo -e "\n${BLUE}🚨 VM 환경 추가 설정 안내:${NC}"
echo -e "${YELLOW}VirtualBox:${NC} 네트워크 > 고급 > 포트 포워딩"
echo -e "  호스트 IP: 127.0.0.1, 호스트 포트: 3000, 게스트 포트: 3000"
echo -e "  호스트 IP: 127.0.0.1, 호스트 포트: 8000, 게스트 포트: 8000"

echo -e "\n${YELLOW}⚠️  종료하려면 Ctrl+C를 누르세요${NC}"
echo -e "${BLUE}================================================${NC}"

# 7. 프론트엔드 실행 (포그라운드)
PORT=3000 npm run dev
