#!/bin/bash

# VM의 외부 IP 확인 스크립트

echo "=== VM IP 주소 확인 ==="
echo ""

echo "1. 공인 IP 주소:"
curl -s ifconfig.me
echo ""
echo ""

echo "2. 내부 네트워크 IP 주소:"
ip route get 1.1.1.1 | awk '{print $7}' | head -1
echo ""

echo "3. 모든 네트워크 인터페이스:"
ip addr show | grep -E 'inet [0-9]' | grep -v '127.0.0.1'
echo ""

echo "=== 사용 방법 ==="
echo "1. 위에서 확인한 IP 주소를 복사하세요"
echo "2. .env 파일에서 YOUR_VM_IP를 실제 IP로 변경하세요"
echo "3. 예: sed -i 's/YOUR_VM_IP/192.168.1.100/g' .env"
echo "" 