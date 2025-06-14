#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 서비스 디버깅 정보${NC}"
echo "=========================="

# 프로세스 확인
echo -e "\n${YELLOW}📋 실행 중인 프로세스:${NC}"
ps aux | grep -E "(uvicorn|next|node)" | grep -v grep || echo "실행 중인 서비스가 없습니다."

# 포트 확인 (더 정확한 방법)
echo -e "\n${YELLOW}🌐 포트 사용 현황 (netstat):${NC}"
echo "포트 8000 (백엔드):"
netstat -tlnp | grep :8000 || echo "포트 8000 사용 중이지 않음"
echo "포트 3000 (프론트엔드):"
netstat -tlnp | grep :3000 || echo "포트 3000 사용 중이지 않음"

# ss 명령으로도 확인
echo -e "\n${YELLOW}🌐 포트 사용 현황 (ss):${NC}"
echo "포트 8000:"
ss -tlnp | grep :8000 || echo "포트 8000 사용 중이지 않음"
echo "포트 3000:"
ss -tlnp | grep :3000 || echo "포트 3000 사용 중이지 않음"

# 방화벽 상태 확인
echo -e "\n${YELLOW}🔥 방화벽 상태:${NC}"
if command -v ufw &> /dev/null; then
    echo "UFW 상태:"
    sudo ufw status
else
    echo "UFW가 설치되어 있지 않습니다."
fi

# iptables 확인
echo -e "\n${YELLOW}🔒 iptables 규칙:${NC}"
sudo iptables -L INPUT -n | grep -E "(3000|8000)" || echo "포트 관련 iptables 규칙 없음"

# 네트워크 인터페이스 확인
echo -e "\n${YELLOW}🌐 네트워크 인터페이스:${NC}"
ip addr show | grep -E "(inet |UP|DOWN)" | head -10

# 서비스 상태 확인
echo -e "\n${YELLOW}🔄 서비스 응답 확인:${NC}"
echo "백엔드 (http://localhost:8000):"
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 백엔드 응답 OK${NC}"
else
    echo -e "${RED}❌ 백엔드 응답 없음${NC}"
fi

echo "프론트엔드 (http://localhost:3000):"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 프론트엔드 응답 OK${NC}"
else
    echo -e "${RED}❌ 프론트엔드 응답 없음${NC}"
fi

# 외부 네트워크 인터페이스로 접근 테스트
echo -e "\n${YELLOW}🌍 외부 인터페이스 접근 테스트:${NC}"
EXTERNAL_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
if [ ! -z "$EXTERNAL_IP" ]; then
    echo "외부 IP: $EXTERNAL_IP"
    echo "백엔드 ($EXTERNAL_IP:8000):"
    if curl -s --connect-timeout 3 http://$EXTERNAL_IP:8000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 외부 IP로 백엔드 접근 가능${NC}"
    else
        echo -e "${RED}❌ 외부 IP로 백엔드 접근 불가${NC}"
    fi
    
    echo "프론트엔드 ($EXTERNAL_IP:3000):"
    if curl -s --connect-timeout 3 http://$EXTERNAL_IP:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 외부 IP로 프론트엔드 접근 가능${NC}"
    else
        echo -e "${RED}❌ 외부 IP로 프론트엔드 접근 불가${NC}"
    fi
fi

# 로그 파일 확인
echo -e "\n${YELLOW}📝 로그 파일 상태:${NC}"
if [ -f "logs/backend.log" ]; then
    echo "백엔드 로그 (마지막 5줄):"
    tail -5 logs/backend.log
else
    echo -e "${RED}❌ 백엔드 로그 파일이 없습니다${NC}"
fi

# 환경 파일 확인
echo -e "\n${YELLOW}⚙️  환경 설정 확인:${NC}"
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✅ backend/.env 파일 존재${NC}"
else
    echo -e "${RED}❌ backend/.env 파일 없음${NC}"
fi

if [ -f "frontend/package.json" ]; then
    echo -e "${GREEN}✅ frontend/package.json 파일 존재${NC}"
else
    echo -e "${RED}❌ frontend/package.json 파일 없음${NC}"
fi

# 시스템 정보
echo -e "\n${YELLOW}💻 시스템 정보:${NC}"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"

echo -e "\n${BLUE}=========================="
echo -e "디버깅 정보 출력 완료${NC}"

# 해결방안 제시
echo -e "\n${BLUE}🔧 포트 접속 문제 해결방안:${NC}"
echo "1. 방화벽 포트 열기: sudo ufw allow 3000 && sudo ufw allow 8000"
echo "2. 서비스 재시작: ./scripts/start-all.sh"
echo "3. VM 포트포워딩 설정 확인 (VirtualBox/VMware 등)" 