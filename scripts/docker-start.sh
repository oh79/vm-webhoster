#!/bin/bash

# 웹 호스팅 서비스 Docker 시작 스크립트
# Ubuntu 22.04 LTS 환경에서 실행

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 스크립트 시작
log_info "🚀 웹 호스팅 서비스 Docker 환경 시작"
log_info "================================================"

# 1. 현재 디렉토리 확인
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml 파일을 찾을 수 없습니다."
    log_error "프로젝트 루트 디렉토리에서 스크립트를 실행해주세요."
    exit 1
fi

# 2. Docker 및 Docker Compose 설치 확인
log_info "Docker 환경 확인 중..."

if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않았습니다."
    log_info "Docker 설치 가이드: https://docs.docker.com/engine/install/ubuntu/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose가 설치되지 않았습니다."
    log_info "Docker Compose 설치: sudo apt-get install docker-compose-plugin"
    exit 1
fi

# 3. Docker 서비스 상태 확인
if ! systemctl is-active --quiet docker; then
    log_warning "Docker 서비스가 실행되지 않았습니다. 시작 중..."
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# 4. 사용자 권한 확인
if ! groups $USER | grep -q '\bdocker\b'; then
    log_warning "현재 사용자가 docker 그룹에 속하지 않습니다."
    log_info "다음 명령어를 실행한 후 로그아웃/로그인하세요:"
    log_info "sudo usermod -aG docker \$USER"
    log_info "또는 sudo를 사용하여 스크립트를 실행하세요."
fi

# 5. 환경 변수 설정 파일 확인
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/config.env.example" ]; then
        log_info "환경 변수 파일 생성 중..."
        cp backend/config.env.example backend/.env
        log_success "환경 변수 파일이 생성되었습니다."
    else
        log_warning "환경 변수 파일이 없습니다. 기본값으로 진행합니다."
    fi
fi

# 6. 필요한 디렉토리 생성
log_info "필요한 디렉토리 생성 중..."
mkdir -p nginx/static
mkdir -p scripts
mkdir -p logs

# 7. 시스템 리소스 확인
log_info "시스템 리소스 확인 중..."

# 메모리 확인 (최소 4GB 권장)
total_memory=$(free -g | awk '/^Mem:/{print $2}')
if [ "$total_memory" -lt 4 ]; then
    log_warning "메모리가 부족할 수 있습니다. (현재: ${total_memory}GB, 권장: 4GB 이상)"
fi

# 디스크 공간 확인 (최소 10GB 권장)
available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$available_space" -lt 10 ]; then
    log_warning "디스크 공간이 부족할 수 있습니다. (현재: ${available_space}GB, 권장: 10GB 이상)"
fi

# 7. 기존 컨테이너 정리 (선택사항)
read -p "기존 컨테이너를 정리하시겠습니까? (y/N): " cleanup_choice
if [[ $cleanup_choice =~ ^[Yy]$ ]]; then
    log_info "기존 컨테이너 정리 중..."
    docker compose down --volumes --remove-orphans || true
fi

# 8. VM 관리를 위한 시스템 준비
log_info "VM 관리 환경 준비 중..."

# libvirt 설치 확인
if ! dpkg -l | grep -q libvirt-daemon-system; then
    log_info "libvirt 설치 중..."
    sudo apt-get update
    sudo apt-get install -y libvirt-daemon-system libvirt-clients qemu-kvm
fi

# libvirt 서비스 시작
if ! systemctl is-active --quiet libvirtd; then
    log_info "libvirt 서비스 시작 중..."
    sudo systemctl start libvirtd
    sudo systemctl enable libvirtd
fi

# 사용자를 libvirt 그룹에 추가
if ! groups $USER | grep -q '\blibvirt\b'; then
    log_info "사용자를 libvirt 그룹에 추가 중..."
    sudo usermod -aG libvirt $USER
fi

# 9. Docker 이미지 빌드
log_info "Docker 이미지 빌드 중..."
docker compose build --no-cache

# 10. 서비스 시작
log_info "서비스 시작 중..."
docker compose up -d

# 11. 서비스 상태 확인
log_info "서비스 상태 확인 중..."
sleep 10

# 각 서비스 상태 확인
services=("webhoster_db" "webhoster_backend" "webhoster_nginx" "webhoster_redis")

for service in "${services[@]}"; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service.*Up"; then
        log_success "$service: 실행 중"
    else
        log_error "$service: 실행 실패"
        docker compose logs $service
    fi
done

# 12. 헬스체크 수행
log_info "헬스체크 수행 중..."

# 데이터베이스 연결 확인
if docker compose exec -T db pg_isready -U webhoster_user -d webhoster_db; then
    log_success "데이터베이스: 연결 성공"
else
    log_error "데이터베이스: 연결 실패"
fi

# 백엔드 API 확인
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health | grep -q "200"; then
    log_success "백엔드 API: 응답 성공"
else
    log_error "백엔드 API: 응답 실패"
fi

# Nginx 확인
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200"; then
    log_success "Nginx: 응답 성공"
else
    log_error "Nginx: 응답 실패"
fi

# 13. 완료 메시지 및 사용 가이드
log_success "🎉 웹 호스팅 서비스 Docker 환경이 성공적으로 시작되었습니다!"
echo
log_info "📋 서비스 접속 정보:"
echo "   • 웹 인터페이스: http://localhost"
echo "   • API 문서: http://localhost:8000/docs"
echo "   • 백엔드 API: http://localhost:8000/api/v1/"
echo "   • 데이터베이스: localhost:5432 (webhoster_db)"
echo "   • Redis: localhost:6379"
echo
log_info "🔧 관리 명령어:"
echo "   • 로그 확인: docker compose logs -f"
echo "   • 서비스 중지: docker compose down"
echo "   • 서비스 재시작: docker compose restart"
echo "   • 컨테이너 상태: docker compose ps"
echo
log_info "🧪 테스트 계정:"
echo "   • 이메일: test@example.com"
echo "   • 비밀번호: testpass123"
echo
log_info "📚 추가 정보는 README.md 파일을 참고하세요."

# 14. 브라우저 열기 (선택사항)
read -p "브라우저를 열어 서비스에 접속하시겠습니까? (y/N): " browser_choice
if [[ $browser_choice =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost
    elif command -v open &> /dev/null; then
        open http://localhost
    else
        log_info "브라우저를 수동으로 열어 http://localhost에 접속하세요."
    fi
fi

log_success "스크립트 실행이 완료되었습니다." 