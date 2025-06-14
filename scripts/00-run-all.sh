#!/bin/bash

# 🚀 웹 호스팅 서비스 통합 설치 스크립트
# 모든 단계를 순차적으로 실행합니다

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 스크립트 시작 시간
START_TIME=$(date +%s)

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

# 배너 출력
clear
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║            🚀 웹 호스팅 서비스 통합 설치 스크립트                    ║"
echo "║                                                                      ║"
echo "║  SSH VM 환경에서 완전한 웹 호스팅 서비스를 자동으로 설치합니다.       ║"
echo "║                                                                      ║"
echo "║  실행될 단계:                                                        ║"
echo "║  1️⃣  시스템 초기 설정 (패키지, Docker, 데이터베이스)                  ║"
echo "║  2️⃣  프로젝트 다운로드 및 환경 설정                                   ║"
echo "║  3️⃣  의존성 설치 (Python, Node.js)                                  ║"
echo "║  4️⃣  데이터베이스 초기화 및 마이그레이션                              ║"
echo "║  5️⃣  네트워크 및 방화벽 설정                                         ║"
echo "║  6️⃣  서비스 시작 (백엔드, 프론트엔드)                                ║"
echo "║  7️⃣  전체 서비스 테스트 및 검증                                      ║"
echo "║                                                                      ║"
echo "║  예상 소요 시간: 25-40분                                             ║"
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

# 단계별 실행
TOTAL_STEPS=7
FAILED_STEPS=0

# 단계 실행 함수
run_step() {
    local step_num=$1
    local step_name="$2"
    local script_path="$3"
    
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║ ${step_num}/${TOTAL_STEPS}: ${step_name}${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
    
    local step_start=$(date +%s)
    
    if [ -f "$script_path" ]; then
        if bash "$script_path"; then
            local step_end=$(date +%s)
            local step_duration=$((step_end - step_start))
            log_success "단계 $step_num 완료! (소요시간: ${step_duration}초)"
        else
            log_error "단계 $step_num 실패: $step_name"
            FAILED_STEPS=$((FAILED_STEPS + 1))
            
            # 사용자에게 계속 진행할지 물어보기
            echo ""
            read -p "⚠️  이 단계가 실패했습니다. 계속 진행하시겠습니까? (y/N): " continue_confirm
            if [[ ! $continue_confirm =~ ^[Yy]$ ]]; then
                log_error "설치가 중단되었습니다."
                exit 1
            fi
        fi
    else
        log_error "스크립트를 찾을 수 없습니다: $script_path"
        FAILED_STEPS=$((FAILED_STEPS + 1))
    fi
}

# 각 단계 실행
run_step 1 "시스템 초기 설정" "./scripts/01-system-setup.sh"
run_step 2 "프로젝트 다운로드 및 설정" "./scripts/02-project-setup.sh"
run_step 3 "의존성 설치" "./scripts/03-dependencies.sh"
run_step 4 "데이터베이스 초기화" "./scripts/04-database-init.sh"
run_step 5 "네트워크 및 방화벽 설정" "./scripts/05-network-setup.sh"
run_step 6 "서비스 시작" "./scripts/06-start-services.sh"
run_step 7 "서비스 테스트" "./scripts/07-test-services.sh"

# 설치 완료
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
MINUTES=$((TOTAL_DURATION / 60))
SECONDS=$((TOTAL_DURATION % 60))

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                           🎉 설치 완료! 🎉                            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo "📊 설치 결과:"
echo "  - 총 소요 시간: ${MINUTES}분 ${SECONDS}초"
echo "  - 완료된 단계: $((TOTAL_STEPS - FAILED_STEPS))/$TOTAL_STEPS"
if [ $FAILED_STEPS -gt 0 ]; then
    echo -e "  - ${YELLOW}실패한 단계: $FAILED_STEPS개${NC}"
else
    echo -e "  - ${GREEN}모든 단계 성공!${NC}"
fi

echo ""
echo "🌐 접속 정보:"
VM_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1 2>/dev/null || echo "감지실패")

echo "  📱 로컬 접속:"
echo "    - 메인 사이트: http://localhost"
echo "    - 백엔드 API: http://localhost:8000/docs" 
echo "    - 프론트엔드: http://localhost:3000"

if [ "$VM_IP" != "감지실패" ] && [ ! -z "$VM_IP" ]; then
    echo ""
    echo "  🌍 VM 접속 (외부에서):"
    echo "    - 메인 사이트: http://$VM_IP"
    echo "    - 백엔드 API: http://$VM_IP:8000/docs"
    echo "    - 프론트엔드: http://$VM_IP:3000"
fi

echo ""
echo "🔐 기본 계정:"
echo "  - 관리자: admin@example.com / admin123"
echo "  - 테스트: test@example.com / test123456"

echo ""
echo "🛠️ 유용한 명령어:"
echo "  - 로그 확인: tail -f logs/*.log"
echo "  - 서비스 상태: ./scripts/debug-services.sh"
echo "  - 서비스 중지: ./scripts/stop-all.sh"
echo "  - 테스트 실행: ./scripts/07-test-services.sh"

echo ""
if [ $FAILED_STEPS -eq 0 ]; then
    echo -e "${GREEN}✅ 웹 호스팅 서비스가 성공적으로 설치되었습니다!${NC}"
    echo -e "${GREEN}🎯 이제 브라우저에서 위의 URL들로 접속해보세요.${NC}"
else
    echo -e "${YELLOW}⚠️  일부 단계에서 오류가 발생했습니다.${NC}"
    echo -e "${YELLOW}🔧 로그를 확인하고 수동으로 문제를 해결하세요.${NC}"
fi

echo ""
echo -e "${BLUE}📚 더 자세한 정보는 ./scripts/README.md 파일을 참조하세요.${NC}" 