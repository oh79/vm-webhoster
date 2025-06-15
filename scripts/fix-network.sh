#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 네트워크 접속 문제 자동 해결${NC}"
echo "========================================="

# 1. 방화벽 설정 확인 및 포트 열기
echo -e "\n${YELLOW}🔥 방화벽 설정 중...${NC}"
if command -v ufw &> /dev/null; then
    echo "UFW 포트 8000, 3000 열기..."
    sudo ufw allow 8000/tcp
    sudo ufw allow 3000/tcp
    echo -e "${GREEN}✅ UFW 포트 설정 완료${NC}"
    
    echo "현재 UFW 상태:"
    sudo ufw status
else
    echo -e "${YELLOW}⚠️  UFW가 설치되어 있지 않습니다${NC}"
fi

# 2. iptables 직접 설정 (UFW 백업)
echo -e "\n${YELLOW}🔒 iptables 직접 설정...${NC}"
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT
echo -e "${GREEN}✅ iptables 규칙 추가 완료${NC}"

# 3. 시스템 포트 바인딩 확인
echo -e "\n${YELLOW}🌐 시스템 포트 바인딩 확인...${NC}"
echo "net.ipv4.ip_forward 설정:"
sysctl net.ipv4.ip_forward

# 필요시 IP forwarding 활성화
if [ "$(sysctl -n net.ipv4.ip_forward)" != "1" ]; then
    echo "IP forwarding 활성화 중..."
    echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
fi

# 4. 네트워크 서비스 재시작
echo -e "\n${YELLOW}🔄 네트워크 서비스 재시작...${NC}"
sudo systemctl restart networking 2>/dev/null || echo "networking 서비스 재시작 불가"

# 5. 현재 포트 상태 확인
echo -e "\n${YELLOW}📋 포트 상태 최종 확인...${NC}"
echo "포트 8000:"
netstat -tlnp | grep :8000 || echo "포트 8000 바인딩되지 않음"
echo "포트 3000:"
netstat -tlnp | grep :3000 || echo "포트 3000 바인딩되지 않음"

# 6. VM/클라우드 환경 안내
echo -e "\n${BLUE}🚨 추가 확인 사항:${NC}"
echo "1. VM 환경인 경우:"
echo "   - VirtualBox: 네트워크 > 고급 > 포트 포워딩 설정"
echo "   - VMware: VM 설정 > 네트워크 > NAT 설정"
echo ""
echo "2. 클라우드 환경인 경우:"
echo "   - AWS: Security Group에서 8000, 3000 포트 인바운드 허용"
echo "   - GCP: 방화벽 규칙에서 tcp:8000,3000 허용"
echo "   - Azure: NSG에서 포트 8000, 3000 허용"
echo ""
echo "3. 로컬 개발 환경:"
echo "   - localhost 대신 VM의 실제 IP 주소 사용"
echo "   - IP 확인: ip addr show"

# 7. 접속 테스트 URL 출력
EXTERNAL_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
if [ ! -z "$EXTERNAL_IP" ]; then
    echo -e "\n${GREEN}🌍 접속 테스트 URL:${NC}"
    echo "백엔드: http://$EXTERNAL_IP:8000/docs"
    echo "프론트엔드: http://$EXTERNAL_IP:3000"
fi

echo -e "\n${GREEN}✅ 네트워크 설정 완료!"
echo -e "서비스를 재시작하려면: ./scripts/start-all.sh${NC}" 