#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔗 SSH 포트포워딩 설정 도우미${NC}"
echo "====================================="

# VM IP 자동 감지
VM_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
CURRENT_USER=$(whoami)

echo -e "${YELLOW}현재 VM 정보:${NC}"
echo "VM IP: $VM_IP"
echo "사용자: $CURRENT_USER"

echo -e "\n${BLUE}📋 로컬 머신에서 실행할 명령어들:${NC}"
echo "======================================="

echo -e "\n${YELLOW}1. SSH 포트포워딩으로 새 연결 (권장):${NC}"
echo "ssh -L 3000:localhost:3000 -L 8000:localhost:8000 $CURRENT_USER@$VM_IP"

echo -e "\n${YELLOW}2. 백그라운드 SSH 터널만 생성:${NC}"
echo "ssh -f -N -L 3000:localhost:3000 -L 8000:localhost:8000 $CURRENT_USER@$VM_IP"

echo -e "\n${YELLOW}3. SSH config 파일 설정 (~/.ssh/config):${NC}"
cat << EOF
Host vm-webhoster
    HostName $VM_IP
    User $CURRENT_USER
    LocalForward 3000 localhost:3000
    LocalForward 8000 localhost:8000
EOF

echo -e "\n${GREEN}✅ 설정 후 로컬에서 접속:${NC}"
echo "프론트엔드: http://localhost:3000"
echo "백엔드: http://localhost:8000/docs"

echo -e "\n${RED}⚠️  주의사항:${NC}"
echo "- 위 명령어는 로컬 머신에서 실행하세요"
echo "- SSH 연결이 끊어지면 포트포워딩도 중단됩니다"
echo "- 백그라운드 터널은 'ps aux | grep ssh'로 확인 가능합니다"

# 현재 SSH 연결 정보 표시
echo -e "\n${BLUE}🔍 현재 SSH 연결 확인:${NC}"
if [ ! -z "$SSH_CLIENT" ]; then
    SSH_CLIENT_IP=$(echo $SSH_CLIENT | awk '{print $1}')
    echo "SSH 클라이언트 IP: $SSH_CLIENT_IP"
    echo -e "${GREEN}✅ SSH 연결 활성화됨${NC}"
else
    echo -e "${YELLOW}⚠️  SSH 환경이 감지되지 않음${NC}"
fi 