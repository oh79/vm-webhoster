#!/bin/bash

# 🚀 웹 호스팅 서비스 통합 설치 스크립트 (개선판)
# 모든 단계를 순차적으로 실행합니다

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
INSTALL_LOG="$LOG_DIR/install.log"

# 스크립트 시작 시간
START_TIME=$(date +%s)

# 로그 함수들
log_info() { 
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$INSTALL_LOG"
}
log_success() { 
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$INSTALL_LOG"
}
log_warning() { 
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$INSTALL_LOG"
}
log_error() { 
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$INSTALL_LOG"
}
log_step() { 
    echo -e "${PURPLE}[STEP]${NC} $1" | tee -a "$INSTALL_LOG"
}

# 진행률 표시 함수
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\r${CYAN}["
    printf "%*s" $filled | tr ' ' '█'
    printf "%*s" $empty | tr ' ' '░'
    printf "] %d%% (%d/%d)${NC}" $percentage $current $total
}

# 데이터베이스 상태 확인 함수
check_database_ready() {
    local max_attempts=5
    local attempt=1
    
    log_info "데이터베이스 연결 상태 확인 중..."
    
    while [ $attempt -le $max_attempts ]; do
        log_info "데이터베이스 연결 시도 $attempt/$max_attempts"
        
        # PostgreSQL 서비스 상태 확인
        if ! systemctl is-active --quiet postgresql; then
            log_warning "PostgreSQL 서비스가 실행되지 않음. 시작 중..."
            sudo systemctl start postgresql
            sleep 3
        fi
        
        # 데이터베이스 연결 테스트
        if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw webhoster_db; then
            log_success "데이터베이스 연결 확인됨"
            return 0
        else
            log_warning "데이터베이스가 존재하지 않습니다. 생성 시도 중..."
            
            # 데이터베이스 및 사용자 생성
            sudo -u postgres psql << 'EOF' 2>/dev/null || true
\set ON_ERROR_STOP off
DROP DATABASE IF EXISTS webhoster_db;
DROP USER IF EXISTS webhoster_user;
CREATE DATABASE webhoster_db;
CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';
GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;
ALTER USER webhoster_user CREATEDB;
ALTER DATABASE webhoster_db OWNER TO webhoster_user;
\q
EOF
            
            sleep 2
            
            # 재확인
            if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw webhoster_db; then
                log_success "데이터베이스 생성 및 연결 확인됨"
                return 0
            fi
        fi
        
        attempt=$((attempt + 1))
        if [ $attempt -le $max_attempts ]; then
            log_info "3초 후 재시도..."
            sleep 3
        fi
    done
    
    log_error "데이터베이스 연결 실패. 수동 확인이 필요합니다."
    return 1
}

# 사전 검사 함수 (개선)
pre_check() {
    log_info "설치 사전 검사를 시작합니다..."
    
    # 로그 디렉토리 생성
    mkdir -p "$LOG_DIR"
    
    # 운영체제 확인
    if [[ ! -f /etc/os-release ]]; then
        log_error "지원하지 않는 운영체제입니다."
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_warning "Ubuntu가 아닌 시스템에서는 일부 기능이 제대로 작동하지 않을 수 있습니다."
    fi
    
    # 권한 확인
    if [[ $EUID -eq 0 ]]; then
        log_error "root 사용자로 실행하지 마세요. sudo 권한을 가진 일반 사용자로 실행하세요."
        exit 1
    fi
    
    # sudo 권한 확인
    if ! sudo -n true 2>/dev/null; then
        log_info "sudo 권한을 확인하고 있습니다..."
        sudo -v
    fi
    
    # 필수 디렉토리 확인
    if [[ ! -d "$PROJECT_ROOT/backend" ]] || [[ ! -d "$PROJECT_ROOT/frontend" ]]; then
        log_error "프로젝트 구조가 올바르지 않습니다. backend와 frontend 디렉토리가 필요합니다."
        exit 1
    fi
    
    # 환경변수 파일 확인 및 생성
    if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
        log_info "환경변수 파일이 없습니다. local.env에서 복사합니다..."
        if [ -f "$PROJECT_ROOT/local.env" ]; then
            cp "$PROJECT_ROOT/local.env" "$PROJECT_ROOT/backend/.env"
            log_success "환경변수 파일 생성 완료"
        else
            log_error "local.env 파일을 찾을 수 없습니다."
            exit 1
        fi
    fi
    
    # 데이터베이스 사전 설정
    check_database_ready
    
    log_success "사전 검사 완료"
}

# 배너 출력
clear
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║            🚀 웹 호스팅 서비스 통합 설치 스크립트 (완전판)          ║"
echo "║                                                                      ║"
echo "║  SSH VM 환경에서 완전한 웹 호스팅 서비스를 자동으로 설치합니다.       ║"
echo "║                                                                      ║"
echo "║  실행될 단계:                                                        ║"
echo "║  1️⃣  시스템 초기 설정 (패키지, Docker, VM 도구, 데이터베이스)         ║"
echo "║  2️⃣  프로젝트 설정 및 환경변수 구성                                  ║"
echo "║  3️⃣  의존성 설치 (Python, Node.js, Redis, requests)                ║"
echo "║  4️⃣  데이터베이스 초기화 및 마이그레이션                              ║"
echo "║  5️⃣  네트워크 및 방화벽 설정                                         ║"
echo "║  6️⃣  서비스 시작 (백엔드, 프론트엔드)                                ║"
echo "║  7️⃣  전체 서비스 테스트 및 검증                                      ║"
echo "║                                                                      ║"
echo "║  🎯 포함된 VM 생성 도구 (완전 자동화):                               ║"
echo "║     ✅ Docker (컨테이너 관리)                                        ║"
echo "║     ✅ KVM/QEMU (가상화 엔진)                                        ║"
echo "║     ✅ libvirt (VM 관리 API)                                         ║"
echo "║     ✅ cloud-init (자동 OS 설정)                                     ║"
echo "║     ✅ Nginx (프록시 및 호스팅)                                      ║"
echo "║     ✅ Python Jinja2 (템플릿 엔진)                                   ║"
echo "║                                                                      ║"
echo "║  🔧 해결된 문제들:                                                   ║"
echo "║     ✅ Docker 권한 자동 설정                                         ║"
echo "║     ✅ Nginx PID 파일 문제 해결                                      ║"
echo "║     ✅ requests 모듈 자동 설치                                       ║"
echo "║     ✅ VM 환경 자동 검증                                             ║"
echo "║                                                                      ║"
echo "║  예상 소요 시간: 15-25분                                             ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 사용자 확인
echo ""
read -p "🚀 전체 설치를 시작하시겠습니까? 이 과정은 시간이 오래 걸릴 수 있습니다. (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    log_info "설치가 취소되었습니다."
    exit 0
fi

echo ""
log_info "설치를 시작합니다... 중간에 중단하지 마세요!"
echo ""

# 사전 검사 실행
pre_check

# 단계별 실행
TOTAL_STEPS=7
FAILED_STEPS=0
SUCCESS_STEPS=0

# 단계 정보 배열 (02-project-setup.sh 추가)
declare -a STEP_NAMES=(
    "시스템 초기 설정 (VM 도구 포함)"
    "프로젝트 설정 및 환경변수 구성"
    "의존성 설치"
    "데이터베이스 초기화"
    "네트워크 및 방화벽 설정"
    "서비스 시작"
    "서비스 테스트"
)

declare -a STEP_SCRIPTS=(
    "./scripts/01-system-setup.sh"
    "./scripts/02-project-setup.sh"
    "./scripts/03-dependencies.sh"
    "./scripts/04-database-init.sh"
    "./scripts/05-network-setup.sh"
    "./scripts/06-start-services.sh"
    "./scripts/07-test-services.sh"
)

# 단계 실행 함수 (개선판)
run_step() {
    local step_num=$1
    local step_name="$2"
    local script_path="$3"
    
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║ ${BOLD}단계 ${step_num}/${TOTAL_STEPS}: ${step_name}${NC}${CYAN}${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
    
    # 진행률 표시
    show_progress $((step_num - 1)) $TOTAL_STEPS
    echo ""
    
    local step_start=$(date +%s)
    local step_log="$LOG_DIR/step-${step_num}.log"
    
    if [ -f "$script_path" ]; then
        log_info "실행 중: $script_path"
        
        # 스크립트 실행 (로그 기록)
        if bash "$script_path" 2>&1 | tee "$step_log"; then
            local step_end=$(date +%s)
            local step_duration=$((step_end - step_start))
            SUCCESS_STEPS=$((SUCCESS_STEPS + 1))
            
            # 진행률 업데이트
            show_progress $step_num $TOTAL_STEPS
            echo ""
            log_success "단계 $step_num 완료! (소요시간: ${step_duration}초)"
            
            return 0
        else
            local step_end=$(date +%s)
            local step_duration=$((step_end - step_start))
            FAILED_STEPS=$((FAILED_STEPS + 1))
            
            log_error "단계 $step_num 실패: $step_name (소요시간: ${step_duration}초)"
            log_error "자세한 로그: $step_log"
            
            # 실패한 단계에 대한 상세 정보 제공
            echo ""
            echo -e "${YELLOW}╭─ 실패 상세 정보 ─────────────────────────────────────────────────╮${NC}"
            echo -e "${YELLOW}│ 단계: $step_name${NC}"
            echo -e "${YELLOW}│ 로그 파일: $step_log${NC}"
            echo -e "${YELLOW}│ 스크립트: $script_path${NC}"
            echo -e "${YELLOW}╰─────────────────────────────────────────────────────────────────╯${NC}"
            
            # 계속 진행 여부 확인
            echo ""
            echo "선택 옵션:"
            echo "1) 계속 진행 (c/continue)"
            echo "2) 재시도 (r/retry)"
            echo "3) 설치 중단 (q/quit)"
            echo ""
            
            while true; do
                read -p "선택하세요 [c/r/q]: " choice
                case $choice in
                    [Cc]|continue)
                        log_warning "단계 $step_num을 건너뛰고 계속 진행합니다."
                        return 1
                        ;;
                    [Rr]|retry)
                        log_info "단계 $step_num을 재시도합니다..."
                        FAILED_STEPS=$((FAILED_STEPS - 1))
                        run_step "$step_num" "$step_name" "$script_path"
                        return $?
                        ;;
                    [Qq]|quit)
                        log_error "사용자 요청으로 설치가 중단되었습니다."
                        exit 1
                        ;;
                    *)
                        echo "잘못된 선택입니다. c, r, 또는 q를 입력하세요."
                        ;;
                esac
            done
        fi
    else
        log_error "스크립트를 찾을 수 없습니다: $script_path"
        FAILED_STEPS=$((FAILED_STEPS + 1))
        return 1
    fi
}

# 각 단계 실행
log_info "총 $TOTAL_STEPS 단계의 설치를 시작합니다."
echo ""

for i in $(seq 0 $((TOTAL_STEPS - 1))); do
    step_num=$((i + 1))
    run_step "$step_num" "${STEP_NAMES[$i]}" "${STEP_SCRIPTS[$i]}"
done

# 최종 진행률 표시
show_progress $TOTAL_STEPS $TOTAL_STEPS
echo ""

# 🔧 최종 환경 검증 및 최적화
if [ $FAILED_STEPS -eq 0 ]; then
    echo ""
    echo -e "${CYAN}🔧 최종 환경 검증 및 최적화 중...${NC}"
    
    # VM 도구 검증
    if [ -f "scripts/check-vm-tools.sh" ]; then
        echo "📋 VM 환경 검증 실행 중..."
        ./scripts/check-vm-tools.sh || log_warning "VM 환경 검증에서 일부 경고가 발생했습니다."
    fi
    
    # nginx 상태 최종 확인
    if sudo systemctl is-active --quiet nginx; then
        echo "✅ Nginx 서비스: 정상 실행 중"
        
        # nginx 리로드 테스트
        if sudo systemctl reload nginx 2>/dev/null; then
            echo "✅ Nginx 리로드: 정상 작동"
        else
            echo "⚠️  Nginx 리로드: 문제 발생 - 재시작으로 복구"
            sudo systemctl restart nginx 2>/dev/null || true
        fi
    else
        echo "❌ Nginx 서비스: 문제 발생"
    fi
    
    # Docker 권한 최종 확인
    if docker ps >/dev/null 2>&1; then
        echo "✅ Docker 권한: 정상"
    else
        echo "⚠️  Docker 권한: 문제 발생 - 권한 재설정"
        sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
    fi
    
    echo -e "${CYAN}🔧 최종 검증 완료${NC}"
fi

# 설치 완료 정보
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
MINUTES=$((TOTAL_DURATION / 60))
SECONDS=$((TOTAL_DURATION % 60))

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
if [ $FAILED_STEPS -eq 0 ]; then
    echo -e "${GREEN}║                     🎉 설치 완전히 성공! 🎉                         ║${NC}"
else
    echo -e "${YELLOW}║                     ⚠️  설치 부분적 완료 ⚠️                        ║${NC}"
fi
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo "📊 설치 결과 요약:"
echo "  ┌─────────────────────────────────────────────┐"
echo "  │ 총 소요 시간: ${MINUTES}분 ${SECONDS}초"
echo "  │ 성공한 단계: ${SUCCESS_STEPS}/${TOTAL_STEPS}"
if [ $FAILED_STEPS -gt 0 ]; then
    echo "  │ 실패한 단계: $FAILED_STEPS개"
    echo "  │ 성공률: $((SUCCESS_STEPS * 100 / TOTAL_STEPS))%"
else
    echo "  │ 성공률: 100% 🎯"
fi
echo "  └─────────────────────────────────────────────┘"

echo ""
echo "🌐 서비스 접속 정보:"
VM_IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7}' | head -1 || echo "자동감지실패")

echo "  📱 로컬 접속:"
echo "    ├─ 메인 사이트: http://localhost"
echo "    ├─ 백엔드 API: http://localhost:8000/docs" 
echo "    └─ 프론트엔드: http://localhost:3000"

if [ "$VM_IP" != "자동감지실패" ] && [ ! -z "$VM_IP" ]; then
    echo ""
    echo "  🌍 외부 접속 (VM IP: $VM_IP):"
    echo "    ├─ 메인 사이트: http://$VM_IP"
    echo "    ├─ 백엔드 API: http://$VM_IP:8000/docs"
    echo "    └─ 프론트엔드: http://$VM_IP:3000"
fi

echo ""
echo "🔐 기본 계정 정보:"
echo "  ├─ 관리자: admin@example.com / admin123"
echo "  └─ 테스트: test@example.com / test123456"

echo ""
echo "🛠️  유용한 명령어:"
echo "  ├─ 전체 로그 확인: tail -f $INSTALL_LOG"
echo "  ├─ 단계별 로그: ls -la $LOG_DIR/"
echo "  ├─ 서비스 상태: ./scripts/debug-services.sh"
echo "  ├─ 서비스 중지: ./scripts/stop-all.sh"
echo "  ├─ 서비스 재시작: ./scripts/restart-all.sh"
echo "  └─ 테스트 재실행: ./scripts/07-test-services.sh"

if [ $FAILED_STEPS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 웹 호스팅 서비스가 성공적으로 설치되었습니다!${NC}"
    echo -e "${GREEN}🎯 이제 브라우저에서 위의 URL들로 접속해보세요.${NC}"
    echo -e "${GREEN}📋 서비스가 완전히 시작되기까지 1-2분 정도 기다려주세요.${NC}"
    echo ""
    echo -e "${BLUE}🔧 자동으로 해결된 문제들:${NC}"
    echo -e "${BLUE}   ✅ VM 생성 도구 완전 설치 및 설정${NC}"
    echo -e "${BLUE}   ✅ Docker 권한 문제 자동 해결${NC}"
    echo -e "${BLUE}   ✅ Nginx PID 파일 문제 자동 해결${NC}"
    echo -e "${BLUE}   ✅ requests 모듈 누락 문제 자동 해결${NC}"
    echo -e "${BLUE}   ✅ Nginx 프록시 설정 자동 구성${NC}"
    echo -e "${BLUE}   ✅ VM 환경 검증 자동 실행${NC}"
    echo ""
    echo -e "${CYAN}🚀 이제 웹사이트에서 \"호스팅 생성\" 버튼을 클릭하여${NC}"
    echo -e "${CYAN}   VM 인스턴스를 생성할 수 있습니다!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  일부 단계에서 오류가 발생했습니다.${NC}"
    echo -e "${YELLOW}🔧 다음 명령어로 문제를 진단하고 해결하세요:${NC}"
    echo -e "${YELLOW}   sudo ./scripts/debug-services.sh${NC}"
    echo -e "${YELLOW}   tail -f $LOG_DIR/step-*.log${NC}"
    echo -e "${YELLOW}   ./scripts/check-vm-tools.sh  # VM 환경 검증${NC}"
    
    echo ""
    echo -e "${CYAN}🔄 실패한 단계만 다시 실행하려면:${NC}"
    for i in $(seq 0 $((TOTAL_STEPS - 1))); do
        step_num=$((i + 1))
        if [ -f "$LOG_DIR/step-${step_num}.log" ]; then
            if ! grep -q "SUCCESS" "$LOG_DIR/step-${step_num}.log" 2>/dev/null; then
                echo -e "   ${STEP_SCRIPTS[$i]}"
            fi
        fi
    done
fi

echo ""
echo -e "${BLUE}📚 더 자세한 정보:${NC}"
echo -e "${BLUE}   └─ ./scripts/README.md${NC}"
echo -e "${BLUE}   └─ ./docs/ 디렉토리의 문서들${NC}"

# 최종 상태에 따른 종료 코드
if [ $FAILED_STEPS -eq 0 ]; then
    exit 0
else
    exit 1
fi 