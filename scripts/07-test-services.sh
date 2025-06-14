#!/bin/bash

# 🚀 7단계: 서비스 테스트 및 검증
# API 테스트, 프론트엔드 테스트, 웹 호스팅 기능 테스트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }
log_test() { echo -e "${CYAN}[TEST]${NC} $1"; }

echo -e "${GREEN}🚀 7단계: 서비스 테스트 및 검증${NC}"
echo "================================================"

# 테스트 결과 변수
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 테스트 함수
run_test() {
    local test_name="$1"
    local test_command="$2"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log_test "테스트: $test_name"
    if eval "$test_command" > /dev/null 2>&1; then
        echo "  ✅ PASS: $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo "  ❌ FAIL: $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# HTTP 테스트 함수
test_http() {
    local url="$1"
    local expected_code="${2:-200}"
    local timeout="${3:-10}"
    
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $timeout "$url")
    [ "$response_code" = "$expected_code" ]
}

# JSON API 테스트 함수
test_api() {
    local url="$1"
    local expected_field="$2"
    local timeout="${3:-10}"
    
    local response=$(curl -s --connect-timeout $timeout "$url")
    echo "$response" | grep -q "$expected_field"
}

# 1. 기본 연결성 테스트
log_step "기본 연결성 테스트"
run_test "인터넷 연결" "ping -c 1 8.8.8.8"
run_test "DNS 해석" "nslookup google.com"
run_test "로컬호스트 접근" "curl -s http://localhost"

# 2. 인프라 서비스 테스트
log_step "인프라 서비스 테스트"
run_test "PostgreSQL 서비스" "systemctl is-active postgresql"
run_test "Redis 서비스" "systemctl is-active redis-server"
run_test "Docker 서비스" "systemctl is-active docker"
run_test "Nginx 서비스" "systemctl is-active nginx"

# 3. 데이터베이스 연결 테스트
log_step "데이터베이스 연결 테스트"
if [ -f "backend/.env" ]; then
    source backend/.env
    run_test "PostgreSQL 연결" "psql '$DATABASE_URL' -c 'SELECT 1;'"
    run_test "Redis 연결" "redis-cli ping"
else
    log_warning "backend/.env 파일을 찾을 수 없어 데이터베이스 테스트를 건너뜁니다."
fi

# 4. 백엔드 API 테스트
log_step "백엔드 API 테스트"
run_test "백엔드 포트 8000" "ss -tlnp | grep -q ':8000'"
run_test "FastAPI 문서 페이지" "test_http 'http://localhost:8000/docs'"
run_test "API 상태 확인" "test_http 'http://localhost:8000/api/v1/health' 200"

# API 엔드포인트 상세 테스트
log_info "API 엔드포인트 상세 테스트..."

# 사용자 등록 테스트
log_test "사용자 등록 API 테스트"
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@example.com",
        "username": "testuser",
        "password": "test123456"
    }' 2>/dev/null || echo "error")

if echo "$REGISTER_RESPONSE" | grep -q '"email"'; then
    echo "  ✅ PASS: 사용자 등록 API"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    
    # 로그인 테스트
    log_test "로그인 API 테스트"
    LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=test@example.com&password=test123456" 2>/dev/null || echo "error")
    
    if echo "$LOGIN_RESPONSE" | grep -q '"access_token"'; then
        echo "  ✅ PASS: 로그인 API"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # 토큰 추출
        ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        
        # 인증된 요청 테스트
        log_test "인증된 사용자 정보 조회"
        USER_INFO=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
            "http://localhost:8000/api/v1/users/me" 2>/dev/null || echo "error")
        
        if echo "$USER_INFO" | grep -q "testuser"; then
            echo "  ✅ PASS: 사용자 정보 조회 API"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo "  ❌ FAIL: 사용자 정보 조회 API"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        
        # 호스팅 생성 테스트
        log_test "웹 호스팅 생성 API 테스트"
        HOSTING_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/host" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"name": "test-hosting"}' 2>/dev/null || echo "error")
        
        if echo "$HOSTING_RESPONSE" | grep -q '"vm_id"'; then
            echo "  ✅ PASS: 웹 호스팅 생성 API"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            
            # 호스팅 정보 추출
            HOSTING_ID=$(echo "$HOSTING_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
            VM_ID=$(echo "$HOSTING_RESPONSE" | grep -o '"vm_id":"[^"]*' | cut -d'"' -f4)
            
            echo "    - 호스팅 ID: $HOSTING_ID"
            echo "    - VM ID: $VM_ID"
            
            # 호스팅 목록 조회 테스트
            log_test "호스팅 목록 조회"
            HOSTING_LIST=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
                "http://localhost:8000/api/v1/host/my" 2>/dev/null || echo "error")
            
            if echo "$HOSTING_LIST" | grep -q "$VM_ID"; then
                echo "  ✅ PASS: 호스팅 목록 조회 API"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                echo "  ❌ FAIL: 호스팅 목록 조회 API"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
            
        else
            echo "  ❌ FAIL: 웹 호스팅 생성 API"
            echo "    Response: $HOSTING_RESPONSE"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        
    else
        echo "  ❌ FAIL: 로그인 API"
        echo "    Response: $LOGIN_RESPONSE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
else
    echo "  ❌ FAIL: 사용자 등록 API"
    echo "    Response: $REGISTER_RESPONSE"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 6))  # API 테스트 6개 추가

# 5. 프론트엔드 테스트
log_step "프론트엔드 테스트"
run_test "프론트엔드 포트 3000" "ss -tlnp | grep -q ':3000'"
run_test "Next.js 메인 페이지" "test_http 'http://localhost:3000'"

# 프론트엔드 페이지 구조 테스트
log_test "프론트엔드 페이지 구조 확인"
FRONTEND_CONTENT=$(curl -s http://localhost:3000 2>/dev/null || echo "error")
if echo "$FRONTEND_CONTENT" | grep -q -i "html\|react\|next"; then
    echo "  ✅ PASS: 프론트엔드 페이지 구조"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "  ❌ FAIL: 프론트엔드 페이지 구조"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# 6. Nginx 프록시 테스트
log_step "Nginx 프록시 테스트"
run_test "Nginx 포트 80" "ss -tlnp | grep -q ':80'"
run_test "Nginx 메인 페이지" "test_http 'http://localhost:80'"
run_test "API 프록시" "test_http 'http://localhost/api/v1/health'"
run_test "문서 프록시" "test_http 'http://localhost/docs'"

# 7. Docker 컨테이너 테스트
log_step "Docker 컨테이너 테스트"
run_test "Docker 실행 권한" "docker ps"

# Docker 컨테이너 목록 확인
log_info "실행 중인 Docker 컨테이너:"
CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker 접근 불가")
if [ "$CONTAINERS" != "Docker 접근 불가" ]; then
    echo "$CONTAINERS"
    
    # 웹호스팅 컨테이너 확인
    WEBHOST_CONTAINERS=$(docker ps --filter "name=webhost-" --format "{{.Names}}" 2>/dev/null || echo "")
    if [ ! -z "$WEBHOST_CONTAINERS" ]; then
        echo "  📦 웹호스팅 컨테이너: $(echo $WEBHOST_CONTAINERS | wc -w)개"
        echo "$WEBHOST_CONTAINERS"
    else
        echo "  📦 웹호스팅 컨테이너: 없음"
    fi
else
    log_warning "Docker 접근 권한이 없습니다. 재로그인이 필요할 수 있습니다."
fi

# 8. 파일시스템 및 권한 테스트
log_step "파일시스템 및 권한 테스트"
run_test "VM 이미지 디렉토리" "[ -d 'backend/vm-images' ]"
run_test "Nginx 설정 디렉토리" "[ -d 'backend/nginx-configs' ]"
run_test "로그 디렉토리" "[ -d 'logs' ]"
run_test "백엔드 가상환경" "[ -d 'backend/venv' ]"
run_test "프론트엔드 의존성" "[ -d 'frontend/node_modules' ]"

# 9. 네트워크 연결 테스트
log_step "네트워크 연결 테스트"
VM_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -1)

if [ ! -z "$VM_IP" ]; then
    log_info "VM IP 주소: $VM_IP"
    run_test "VM IP로 백엔드 접근" "test_http 'http://$VM_IP:8000/docs'"
    run_test "VM IP로 프론트엔드 접근" "test_http 'http://$VM_IP:3000'"
    run_test "VM IP로 Nginx 접근" "test_http 'http://$VM_IP:80'"
else
    log_warning "VM IP 주소를 감지할 수 없습니다."
fi

# 10. 성능 및 리소스 테스트
log_step "성능 및 리소스 테스트"

# 메모리 사용량 확인
MEMORY_USAGE=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2 * 100}')
log_info "메모리 사용률: ${MEMORY_USAGE}%"
if (( $(echo "$MEMORY_USAGE < 90" | bc -l) )); then
    echo "  ✅ 메모리 사용률 양호 (${MEMORY_USAGE}%)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "  ⚠️  메모리 사용률 높음 (${MEMORY_USAGE}%)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# 디스크 사용량 확인
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
log_info "디스크 사용률: ${DISK_USAGE}%"
if [ "$DISK_USAGE" -lt 85 ]; then
    echo "  ✅ 디스크 사용률 양호 (${DISK_USAGE}%)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "  ⚠️  디스크 사용률 높음 (${DISK_USAGE}%)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 2))

# 최종 테스트 결과
log_step "테스트 결과 요약"
echo "════════════════════════════════════════════════"
echo "📊 테스트 결과:"
echo "  - 총 테스트: $TOTAL_TESTS개"
echo "  - 성공: $PASSED_TESTS개 ✅"
echo "  - 실패: $FAILED_TESTS개 ❌"
echo "  - 성공률: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
echo "════════════════════════════════════════════════"

# 접속 정보 재출력
echo ""
echo "🌐 접속 정보:"
echo "  - 메인 사이트: http://localhost (Nginx 프록시)"
echo "  - 백엔드 API: http://localhost:8000/docs"
echo "  - 프론트엔드: http://localhost:3000"

if [ ! -z "$VM_IP" ]; then
    echo "  - VM 직접 접근: http://$VM_IP"
fi

echo ""
echo "🔐 테스트 계정:"
echo "  - 이메일: test@example.com"
echo "  - 비밀번호: test123456"

echo ""
echo "🛠️ 유용한 명령어:"
echo "  - 로그 확인: tail -f logs/*.log"
echo "  - 서비스 상태: ./scripts/debug-services.sh"
echo "  - 서비스 중지: ./scripts/stop-all.sh"

# 테스트 결과에 따른 종료 코드
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 테스트가 성공했습니다!${NC}"
    echo -e "${GREEN}🎉 웹 호스팅 서비스가 정상적으로 구동되고 있습니다.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  일부 테스트가 실패했습니다.${NC}"
    echo -e "${YELLOW}로그를 확인하고 문제를 해결하세요.${NC}"
    exit 1
fi 