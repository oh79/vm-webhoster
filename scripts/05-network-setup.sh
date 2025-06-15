#!/bin/bash

# 🚀 5단계: 네트워크 및 방화벽 설정
# 포트 설정, Nginx 설정, SSH 포워딩 등

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

echo -e "${GREEN}🚀 5단계: 네트워크 및 방화벽 설정${NC}"
echo "================================================"

# VM IP 주소 감지
log_step "네트워크 정보 확인"
VM_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || echo "감지실패")

echo "📡 네트워크 정보:"
echo "  - 내부 IP: ${VM_IP:-'감지실패'}"
echo "  - 외부 IP: $EXTERNAL_IP"
echo "  - 호스트명: $(hostname)"

# 방화벽 설정
log_step "방화벽 포트 설정"
echo "🔥 방화벽 규칙 추가:"

# UFW 방화벽 설정
if command -v ufw &> /dev/null; then
    # 기본 포트들
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp  # 백엔드
    sudo ufw allow 3000/tcp  # 프론트엔드
    
    # VM 호스팅 포트 범위
    sudo ufw allow 8080:8180/tcp  # HTTP 포트 범위
    sudo ufw allow 10022:10100/tcp  # SSH 포트 범위
    
    echo "  ✅ UFW 방화벽 규칙 설정 완료"
else
    log_warning "UFW를 찾을 수 없습니다."
fi

# iptables 직접 설정 (백업)
log_info "iptables 규칙 추가 (백업용)..."
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true

echo "  ✅ iptables 규칙 추가 완료"

# IP 포워딩 활성화
log_step "IP 포워딩 설정"
if [ "$(sysctl -n net.ipv4.ip_forward 2>/dev/null)" != "1" ]; then
    echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf >/dev/null
    sudo sysctl -p >/dev/null
    echo "  ✅ IP 포워딩 활성화 완료"
else
    echo "  ℹ️  IP 포워딩 이미 활성화됨"
fi

# Nginx 설치 및 기본 설정
log_step "Nginx 설치 및 설정"
if ! command -v nginx &> /dev/null; then
    log_info "Nginx 설치 중..."
    sudo apt update
    sudo apt install -y nginx
    log_success "Nginx 설치 완료"
fi

# Nginx 서비스 시작
sudo systemctl start nginx
sudo systemctl enable nginx

# 기본 Nginx 설정 생성
log_info "Nginx 기본 설정 생성..."
sudo tee /etc/nginx/sites-available/webhosting > /dev/null << EOF
# 웹 호스팅 서비스 메인 설정
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    root /var/www/html;
    index index.html index.htm;
    
    # 메인 페이지
    location / {
        try_files \$uri \$uri/ @backend;
    }
    
    # 백엔드 API 프록시
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 백엔드 API 문서
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /redoc {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 프론트엔드로 폴백
    location @backend {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # 정적 파일 캐싱
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# 개별 사용자 VM 호스팅을 위한 include
# include /etc/nginx/conf.d/webhosting-*.conf;

EOF

# 기존 default 사이트 비활성화
sudo rm -f /etc/nginx/sites-enabled/default

# 새 설정 활성화
sudo ln -sf /etc/nginx/sites-available/webhosting /etc/nginx/sites-enabled/

# Nginx 설정 테스트
log_info "Nginx 설정 테스트..."
if sudo nginx -t; then
    log_success "Nginx 설정 테스트 통과"
    sudo systemctl reload nginx
    log_success "Nginx 재로드 완료"
else
    log_error "Nginx 설정에 오류가 있습니다."
    exit 1
fi

# 포트 사용 현황 확인
log_step "포트 사용 현황 확인"
echo "📊 주요 포트 상태:"

# 포트 확인 함수
check_port() {
    local port=$1
    local service=$2
    if ss -tlnp | grep -q ":$port "; then
        echo "  ✅ $service (포트 $port): 사용 중"
    else
        echo "  ❌ $service (포트 $port): 사용 안 함"
    fi
}

check_port 22 "SSH"
check_port 80 "HTTP/Nginx"
check_port 443 "HTTPS"
check_port 3000 "프론트엔드"
check_port 8000 "백엔드"
check_port 5432 "PostgreSQL"
check_port 6379 "Redis"

# 네트워크 연결 테스트
log_step "네트워크 연결 테스트"
echo "🌐 연결성 테스트:"

# 로컬 서비스 테스트
test_connection() {
    local url=$1
    local name=$2
    local timeout=${3:-5}
    
    if curl -s --connect-timeout $timeout "$url" > /dev/null 2>&1; then
        echo "  ✅ $name: 연결 가능"
        return 0
    else
        echo "  ❌ $name: 연결 불가"
        return 1
    fi
}

test_connection "http://localhost:80" "Nginx (로컬)"
test_connection "http://8.8.8.8" "인터넷 연결" 3

# 외부 접근 안내
log_step "외부 접근 설정 안내"
echo "🌍 외부 접근 설정:"
echo "  1. VirtualBox/VMware 포트 포워딩:"
echo "     - 호스트 포트 80 → 게스트 포트 80"
echo "     - 호스트 포트 3000 → 게스트 포트 3000"
echo "     - 호스트 포트 8000 → 게스트 포트 8000"
echo ""
echo "  2. 클라우드 인스턴스 보안 그룹:"
echo "     - HTTP (80)"
echo "     - HTTPS (443)"
echo "     - Custom TCP (3000, 8000)"
echo ""
echo "  3. 방화벽 확인:"
echo "     - sudo ufw status"
echo "     - sudo iptables -L"

# 설정 파일 백업
log_step "설정 파일 백업"
sudo cp /etc/nginx/sites-available/webhosting /etc/nginx/sites-available/webhosting.backup.$(date +%Y%m%d_%H%M%S)
log_success "Nginx 설정 백업 완료"

echo -e "${GREEN}✅ 5단계: 네트워크 및 방화벽 설정 완료${NC}"
echo "================================================"
echo "🔍 네트워크 설정 요약:"
echo "  - 방화벽: 설정됨"
echo "  - Nginx: 설치 및 설정됨"
echo "  - 포트 포워딩: 준비됨"
echo "  - VM IP: ${VM_IP:-'감지실패'}"
echo "다음 단계: ./scripts/06-start-services.sh" 