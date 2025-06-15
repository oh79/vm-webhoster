#!/bin/bash

# 🔍 VM 생성 도구 설치 확인 스크립트
# VM 호스팅에 필요한 모든 도구들이 제대로 설치되었는지 검증합니다

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

echo -e "${GREEN}🔍 VM 생성 도구 설치 확인 스크립트${NC}"
echo "=============================================="

# 검증 결과 카운터
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 도구 검증 함수
check_tool() {
    local tool_name=$1
    local command=$2
    local description=$3
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if command -v "$command" &> /dev/null; then
        local version=$($command --version 2>/dev/null | head -1 || echo "버전 정보 없음")
        log_success "$tool_name: ✅ 설치됨 ($version)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$tool_name: ❌ 설치되지 않음 ($description)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# 서비스 상태 확인 함수
check_service() {
    local service_name=$1
    local description=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if systemctl is-active --quiet "$service_name"; then
        log_success "$service_name 서비스: ✅ 실행 중"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$service_name 서비스: ❌ 실행되지 않음 ($description)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# 사용자 그룹 확인 함수
check_user_group() {
    local group_name=$1
    local description=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if groups $USER | grep -q "$group_name"; then
        log_success "사용자 그룹 $group_name: ✅ 포함됨"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "사용자 그룹 $group_name: ❌ 포함되지 않음 ($description)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo ""
log_step "1. 기본 도구 확인"
check_tool "Docker" "docker" "컨테이너 관리 도구"
check_tool "Node.js" "node" "JavaScript 런타임"
check_tool "Python3" "python3" "Python 인터프리터"
check_tool "PostgreSQL" "psql" "데이터베이스 클라이언트"
check_tool "Redis CLI" "redis-cli" "Redis 클라이언트"

echo ""
log_step "2. VM 생성 도구 확인"
check_tool "libvirt (virsh)" "virsh" "VM 관리 도구"
check_tool "QEMU" "qemu-system-x86_64" "가상화 엔진"
check_tool "qemu-img" "qemu-img" "디스크 이미지 도구"
check_tool "genisoimage" "genisoimage" "ISO 이미지 생성 도구"
check_tool "cloud-localds" "cloud-localds" "cloud-init 도구"

echo ""
log_step "3. 시스템 서비스 확인"
check_service "docker" "Docker 컨테이너 서비스"
check_service "libvirtd" "libvirt 가상화 서비스"
check_service "postgresql" "PostgreSQL 데이터베이스"
check_service "redis-server" "Redis 캐시 서버"

echo ""
log_step "4. 사용자 권한 확인"
check_user_group "docker" "Docker 컨테이너 관리 권한"
check_user_group "libvirt" "VM 관리 권한"
check_user_group "kvm" "KVM 가상화 권한"

echo ""
log_step "5. 가상화 환경 확인"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if grep -q -E '(vmx|svm)' /proc/cpuinfo; then
    log_success "CPU 가상화 지원: ✅ 활성화됨 (VT-x/AMD-V)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_warning "CPU 가상화 지원: ⚠️  감지되지 않음 (BIOS에서 활성화 필요할 수 있음)"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""
log_step "6. 네트워크 환경 확인"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if virsh net-list --all 2>/dev/null | grep -q "default"; then
    log_success "libvirt 기본 네트워크: ✅ 설정됨"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "libvirt 기본 네트워크: ❌ 설정되지 않음"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""
log_step "7. 디렉토리 구조 확인"
for dir in "vm-images/templates" "vm-images/containers" "/var/lib/vm-webhoster"; do
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -d "$dir" ]; then
        log_success "디렉토리 $dir: ✅ 존재함"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "디렉토리 $dir: ❌ 존재하지 않음"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
done

echo ""
log_step "8. Nginx 호스팅 환경 확인"
# nginx 설치 확인
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if command -v nginx &> /dev/null; then
    nginx_version=$(nginx -v 2>&1 | head -1)
    log_success "Nginx: ✅ 설치됨 ($nginx_version)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "Nginx: ❌ 설치되지 않음"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Python Jinja2 확인
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if python3 -c "import jinja2" &> /dev/null; then
    jinja2_version=$(python3 -c "import jinja2; print(jinja2.__version__)" 2>/dev/null || echo "설치됨")
    log_success "Python Jinja2: ✅ 설치됨 (v$jinja2_version)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "Python Jinja2: ❌ 설치되지 않음"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# nginx 호스팅 디렉토리 확인
for dir in "/etc/nginx/sites-available/hosting" "/etc/nginx/sites-enabled/hosting" "/etc/nginx/templates"; do
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -d "$dir" ]; then
        log_success "Nginx 디렉토리 $dir: ✅ 존재함"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "Nginx 디렉토리 $dir: ❌ 존재하지 않음"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
done

# nginx-config-manager.sh 확인
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -f "scripts/nginx-config-manager.sh" ] && [ -x "scripts/nginx-config-manager.sh" ]; then
    log_success "nginx-config-manager.sh: ✅ 실행 가능"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "nginx-config-manager.sh: ❌ 없거나 실행 불가"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# 최종 결과 출력
echo ""
echo "=============================================="
echo -e "${PURPLE}📊 검증 결과 요약${NC}"
echo "=============================================="

PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo "  총 검사 항목: $TOTAL_CHECKS"
echo "  성공: $PASSED_CHECKS"
echo "  실패: $FAILED_CHECKS"
echo "  성공률: $PASS_RATE%"

echo ""
if [ $PASS_RATE -ge 90 ]; then
    echo -e "${GREEN}🎉 VM 생성 환경이 완벽하게 설정되었습니다!${NC}"
    echo -e "${GREEN}✅ 호스팅 인스턴스 생성이 가능합니다.${NC}"
    exit 0
elif [ $PASS_RATE -ge 75 ]; then
    echo -e "${YELLOW}⚠️  VM 생성 환경이 대부분 설정되었습니다.${NC}"
    echo -e "${YELLOW}🔧 일부 항목을 수정하면 더 안정적으로 작동할 것입니다.${NC}"
    exit 1
else
    echo -e "${RED}❌ VM 생성 환경 설정이 불완전합니다.${NC}"
    echo -e "${RED}🛠️  ./scripts/01-system-setup.sh 를 실행하여 설치를 완료하세요.${NC}"
    exit 2
fi

echo ""
echo "💡 문제 해결 방법:"
echo "  1. ./scripts/01-system-setup.sh 실행"
echo "  2. 터미널 재시작 후 다시 확인"
echo "  3. 로그아웃 후 다시 로그인"
echo "  4. newgrp docker && newgrp libvirt 실행" 