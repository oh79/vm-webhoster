#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 연결 테스트 및 진단${NC}"
echo "=========================="

# VM 정보
VM_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
CURRENT_USER=$(whoami)

echo -e "${YELLOW}VM 정보:${NC}"
echo "VM IP: $VM_IP"
echo "사용자: $CURRENT_USER"

# 포트 바인딩 확인
echo -e "\n${YELLOW}🌐 VM 내부 포트 바인딩:${NC}"
ss -tulpn | grep -E "(3000|8000)" || echo "포트가 바인딩되지 않음"

# 로컬 접속 테스트
echo -e "\n${YELLOW}🔄 VM 내부 접속 테스트:${NC}"
echo "포트 3000 테스트:"
if curl -s --connect-timeout 3 http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 포트 3000 응답 OK${NC}"
else
    echo -e "${RED}❌ 포트 3000 응답 없음${NC}"
fi

echo "포트 8000 테스트:"
if curl -s --connect-timeout 3 http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 포트 8000 응답 OK${NC}"
else
    echo -e "${RED}❌ 포트 8000 응답 없음${NC}"
fi

# SSH 환경 확인
echo -e "\n${YELLOW}🔗 SSH 연결 정보:${NC}"
if [ ! -z "$SSH_CLIENT" ]; then
    SSH_CLIENT_IP=$(echo $SSH_CLIENT | awk '{print $1}')
    echo "SSH 클라이언트 IP: $SSH_CLIENT_IP"
    echo -e "${GREEN}✅ SSH 연결 활성화됨${NC}"
    
    echo -e "\n${BLUE}📋 로컬 머신에서 실행할 SSH 포트포워딩:${NC}"
    echo -e "${YELLOW}방법 1 (새 터미널):${NC}"
    echo "ssh -L 3000:localhost:3000 -L 8000:localhost:8000 $CURRENT_USER@$VM_IP"
    echo ""
    echo -e "${YELLOW}방법 2 (백그라운드):${NC}"
    echo "ssh -f -N -L 3000:localhost:3000 -L 8000:localhost:8000 $CURRENT_USER@$VM_IP"
    
else
    echo -e "${YELLOW}⚠️  SSH 환경이 감지되지 않음${NC}"
fi

# 프로세스 확인
echo -e "\n${YELLOW}🔄 실행 중인 서비스:${NC}"
ps aux | grep -E "(next|uvicorn)" | grep -v grep | head -3

echo -e "\n${BLUE}=========================="
echo -e "${YELLOW}⚠️  SSH 포트포워딩 설정 후 로컬에서 접속:${NC}"
echo -e "${GREEN}http://localhost:3000 (프론트엔드)${NC}"
echo -e "${GREEN}http://localhost:8000/docs (백엔드 API)${NC}"
echo -e "${BLUE}==========================${NC}" 