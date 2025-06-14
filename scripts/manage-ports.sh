#!/bin/bash

# 🔧 포트 관리 스크립트
# 불필요한 포트를 정리하고 필요한 포트만 관리합니다

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

show_usage() {
    echo "사용법: $0 [옵션]"
    echo "옵션:"
    echo "  status   - 현재 열린 포트 상태 확인"
    echo "  clean    - 불필요한 포트 정리"
    echo "  list     - 필요한 포트 목록 표시"
    echo "  help     - 이 도움말 표시"
}

show_port_status() {
    log_info "현재 열린 포트 상태:"
    echo
    echo "=== 시스템 포트 (LISTEN) ==="
    ss -tulnp | grep LISTEN | sort -k5
    echo
    echo "=== 프로젝트 관련 포트 ==="
    netstat -tulnp 2>/dev/null | grep -E "(3000|8000|5432|6379)" | grep LISTEN || echo "프로젝트 포트가 열려있지 않습니다."
}

show_required_ports() {
    log_info "웹 호스팅 서비스에 필요한 포트:"
    echo
    echo "🌐 필수 포트:"
    echo "  - 3000: 프론트엔드 (Next.js)"
    echo "  - 8000: 백엔드 API (FastAPI)"
    echo
    echo "🔧 내부 서비스:"
    echo "  - 5432: PostgreSQL 데이터베이스"
    echo "  - 6379: Redis 캐시"
    echo
    echo "🚀 VM 호스팅용 (필요시만):"
    echo "  - 10022-10032: SSH 포트 (최대 10개 VM)"
    echo "  - 8080-8090: HTTP 포트 (최대 10개 웹사이트)"
    echo
    echo "⚠️  기타 포트:"
    echo "  - 22: SSH (시스템 기본)"
    echo "  - 53: DNS (libvirt)"
    echo "  - 80: Nginx (필요시)"
}

clean_ports() {
    log_info "불필요한 포트 정리 중..."
    
    # Node.js 프로세스 중 불필요한 것들 정리 (개발 서버 제외)
    log_info "불필요한 Node.js 프로세스 확인..."
    CURRENT_NEXT_PID=$(pgrep -f "next-server" 2>/dev/null || true)
    NODE_PIDS=$(pgrep -f "node" 2>/dev/null | grep -v "$CURRENT_NEXT_PID" || true)
    
    if [ -n "$NODE_PIDS" ]; then
        echo "발견된 Node.js 프로세스:"
        ps -p $NODE_PIDS -o pid,cmd 2>/dev/null || true
        read -p "이 프로세스들을 종료하시겠습니까? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            echo $NODE_PIDS | xargs kill -TERM 2>/dev/null || true
            log_success "불필요한 Node.js 프로세스 정리 완료"
        else
            log_info "프로세스 정리를 건너뛰었습니다."
        fi
    else
        log_info "정리할 불필요한 Node.js 프로세스가 없습니다."
    fi
    
    # libvirt 네트워크 확인 및 정리
    log_info "libvirt 네트워크 상태 확인..."
    if command -v virsh >/dev/null 2>&1; then
        virsh net-list --all 2>/dev/null || log_warning "libvirt에 접근할 수 없습니다."
    fi
    
    log_success "포트 정리 완료"
}

# 메인 로직
case "$1" in
    "status")
        show_port_status
        ;;
    "clean")
        clean_ports
        ;;
    "list")
        show_required_ports
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    "")
        echo "🔧 포트 관리 스크립트"
        echo
        show_usage
        echo
        log_info "현재 상태를 확인하려면: $0 status"
        log_info "포트를 정리하려면: $0 clean"
        ;;
    *)
        log_error "알 수 없는 옵션: $1"
        show_usage
        exit 1
        ;;
esac 