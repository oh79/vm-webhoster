#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚡ 빠른 네트워크 수정${NC}"
echo "======================"

# 포트 열기
echo -e "${YELLOW}🔥 포트 8000, 3000 열기...${NC}"
sudo ufw allow 8000/tcp >/dev/null 2>&1
sudo ufw allow 3000/tcp >/dev/null 2>&1
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT >/dev/null 2>&1
sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT >/dev/null 2>&1

# IP 정보 출력
EXTERNAL_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
echo -e "${GREEN}✅ 포트 설정 완료!${NC}"
echo -e "${YELLOW}VM IP: $EXTERNAL_IP${NC}"
echo ""
echo -e "${BLUE}🌐 접속 URL:${NC}"
echo "http://$EXTERNAL_IP:8000/docs (백엔드)"
echo "http://$EXTERNAL_IP:3000 (프론트엔드)"
echo ""
echo -e "${YELLOW}⚠️  VM 포트포워딩도 설정하세요!${NC}" 