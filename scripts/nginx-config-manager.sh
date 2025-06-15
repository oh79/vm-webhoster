#!/bin/bash

# Nginx 설정 관리 스크립트 (리팩토링 버전)
# 사용법: ./nginx-config-manager.sh [command] [options]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 기본 경로 설정
NGINX_DIR="/etc/nginx"
PROJECT_NGINX_DIR="$(dirname "$0")/../nginx"
HOSTING_DIR="$NGINX_DIR/sites-available/hosting"
TEMPLATE_FILE="$PROJECT_NGINX_DIR/templates/user-hosting.conf.j2"
LOG_DIR="/var/log/nginx"

# 로깅 함수
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

# 도움말 출력
print_help() {
    cat << EOF
Nginx 설정 관리 스크립트 (리팩토링 버전)

사용법:
  $(basename "$0") <command> [options]

명령어:
  init                    Nginx 설정 디렉토리 초기화
  add-user <user_id>      사용자 호스팅 설정 추가
  remove-user <user_id>   사용자 호스팅 설정 제거
  update-user <user_id>   사용자 호스팅 설정 업데이트
  list-users              등록된 사용자 목록 출력
  validate                Nginx 설정 검증
  reload                  Nginx 설정 리로드
  status                  Nginx 상태 확인
  cleanup                 중복/불필요한 설정 파일 정리
  migrate                 기존 설정을 새 구조로 마이그레이션

옵션:
  --vm-id <vm_id>         VM ID 지정
  --vm-ip <vm_ip>         VM IP 주소 지정 (기본값: 127.0.0.1)
  --web-port <port>       웹 포트 지정
  --ssh-port <port>       SSH 포트 지정
  --dry-run               실제 작업 없이 미리보기만 실행
  --force                 강제 실행 (확인 없이)
  --backup                백업 생성 후 작업

예시:
  $(basename "$0") init
  $(basename "$0") add-user 7 --vm-id vm-abc123 --vm-ip 192.168.122.100 --web-port 8007 --ssh-port 10007
  $(basename "$0") remove-user 7
  $(basename "$0") cleanup --backup
  $(basename "$0") migrate

EOF
}

# 인수 파싱
COMMAND=""
USER_ID=""
VM_ID=""
VM_IP="127.0.0.1"
WEB_PORT=""
SSH_PORT=""
DRY_RUN=false
FORCE=false
BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        init|add-user|remove-user|update-user|list-users|validate|reload|status|cleanup|migrate)
            COMMAND="$1"
            shift
            ;;
        --vm-id)
            VM_ID="$2"
            shift 2
            ;;
        --vm-ip)
            VM_IP="$2"
            shift 2
            ;;
        --web-port)
            WEB_PORT="$2"
            shift 2
            ;;
        --ssh-port)
            SSH_PORT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            # 명령어가 설정된 후 첫 번째 인수는 사용자 ID로 처리
            if [[ -n "$COMMAND" && -z "$USER_ID" && ! "$1" =~ ^-- ]]; then
                USER_ID="$1"
                shift
            else
                log_error "알 수 없는 옵션: $1"
                print_help
                exit 1
            fi
            ;;
    esac
done

# 필수 도구 확인
check_requirements() {
    local missing_tools=()
    
    command -v nginx >/dev/null 2>&1 || missing_tools+=("nginx")
    command -v jinja2 >/dev/null 2>&1 || {
        command -v python3 >/dev/null 2>&1 && python3 -c "import jinja2" 2>/dev/null || missing_tools+=("python3-jinja2")
    }
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "다음 도구들이 필요합니다: ${missing_tools[*]}"
        return 1
    fi
}

# 백업 생성
create_backup() {
    if [[ "$BACKUP" == true ]]; then
        local backup_dir="/tmp/nginx-backup-$(date +%Y%m%d-%H%M%S)"
        log_info "백업 생성 중: $backup_dir"
        
        mkdir -p "$backup_dir"
        cp -r "$NGINX_DIR" "$backup_dir/" 2>/dev/null || true
        
        log_success "백업 완료: $backup_dir"
    fi
}

# Nginx 설정 디렉토리 초기화
init_nginx_config() {
    log_info "Nginx 설정 디렉토리 초기화 중..."
    
    create_backup
    
    # 디렉토리 생성
    mkdir -p "$NGINX_DIR/conf.d"
    mkdir -p "$NGINX_DIR/sites-available/hosting"
    mkdir -p "$LOG_DIR"
    
    # 기본 설정 파일 복사
    if [[ "$DRY_RUN" == false ]]; then
        cp "$PROJECT_NGINX_DIR"/*.conf "$NGINX_DIR/" 2>/dev/null || true
        cp "$PROJECT_NGINX_DIR/conf.d"/*.conf "$NGINX_DIR/conf.d/" 2>/dev/null || true
        cp "$PROJECT_NGINX_DIR/sites-available"/*.conf "$NGINX_DIR/sites-available/" 2>/dev/null || true
    fi
    
    log_success "Nginx 설정 초기화 완료"
}

# 사용자 호스팅 설정 추가
add_user_config() {
    local user_id="$1"
    
    if [[ -z "$user_id" ]]; then
        log_error "사용자 ID가 필요합니다"
        return 1
    fi
    
    # 필수 파라미터 검증
    if [[ -z "$VM_ID" || -z "$WEB_PORT" || -z "$SSH_PORT" ]]; then
        log_error "VM ID, 웹 포트, SSH 포트가 모두 필요합니다"
        return 1
    fi
    
    local config_file="$HOSTING_DIR/${user_id}.conf"
    local main_config_file="$NGINX_DIR/sites-available/main.conf"
    
    # 기존 설정 확인
    if [[ -f "$config_file" && "$FORCE" != true ]]; then
        log_warning "사용자 $user_id의 설정이 이미 존재합니다. --force 옵션을 사용하세요."
        return 1
    fi
    
    log_info "사용자 $user_id 호스팅 설정 생성 중... (IP: $VM_IP, 웹포트: $WEB_PORT)"
    
    if [[ "$DRY_RUN" == false ]]; then
        # 컨테이너 연결 사전 테스트
        if ! test_container_connection "$VM_IP" "$WEB_PORT"; then
            log_warning "컨테이너 연결 테스트 실패: $VM_IP:$WEB_PORT, 계속 진행..."
        fi
        
        # 템플릿을 사용하여 설정 파일 생성
        python3 -c "
import jinja2
from datetime import datetime

template_str = open('$TEMPLATE_FILE').read()
template = jinja2.Template(template_str)

config = template.render(
    user_id='$user_id',
    vm_id='$VM_ID',
    vm_ip='$VM_IP',
    web_port='$WEB_PORT',
    ssh_port='$SSH_PORT',
    creation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
)

with open('$config_file', 'w') as f:
    f.write(config)
"
        
        # 권한 설정
        chmod 644 "$config_file"
        
        # main.conf에 include 추가 (중복 체크)
        if ! grep -q "include $HOSTING_DIR/\*.conf;" "$main_config_file" 2>/dev/null; then
            # main.conf의 server 블록 끝 부분에 include 추가
            sed -i '/# 사용자별 호스팅 사이트 설정/i\\n    # 동적 사용자 호스팅 include\n    include '"$HOSTING_DIR"'/*.conf;\n' "$main_config_file"
        fi
        
        # 설정 검증
        if validate_config; then
            log_success "사용자 $user_id 설정 생성 및 검증 완료: $config_file"
            
            # nginx 리로드
            if systemctl reload nginx 2>/dev/null; then
                log_success "nginx 리로드 완료"
                
                # 실시간 검증 (최대 30초 대기)
                log_info "프록시 규칙 동작 검증 중..."
                if verify_proxy_rule "$user_id" "$VM_IP" "$WEB_PORT"; then
                    log_success "프록시 규칙 검증 성공: 사용자 $user_id"
                else
                    log_warning "프록시 규칙 검증 실패: 사용자 $user_id"
                    # 자동 수정 시도
                    if auto_fix_config "$user_id" "$VM_IP" "$WEB_PORT"; then
                        log_success "설정 자동 수정 완료: 사용자 $user_id"
                    else
                        log_error "설정 자동 수정 실패: 사용자 $user_id"
                    fi
                fi
            else
                log_error "nginx 리로드 실패"
                return 1
            fi
        else
            log_error "nginx 설정 검증 실패"
            return 1
        fi
    else
        log_info "[DRY RUN] 사용자 $user_id 설정 파일이 생성될 예정: $config_file"
    fi
}

# 컨테이너 연결 테스트
test_container_connection() {
    local vm_ip="$1"
    local web_port="$2"
    local timeout=5
    
    if command -v nc >/dev/null 2>&1; then
        # netcat 사용
        if timeout "$timeout" nc -z "$vm_ip" "$web_port" 2>/dev/null; then
            log_info "컨테이너 연결 테스트 성공: $vm_ip:$web_port"
            return 0
        else
            log_warning "컨테이너 연결 테스트 실패: $vm_ip:$web_port"
            return 1
        fi
    else
        # curl 사용 (대체 방법)
        if timeout "$timeout" curl -s --connect-timeout "$timeout" "http://$vm_ip:$web_port" >/dev/null 2>&1; then
            log_info "컨테이너 연결 테스트 성공: $vm_ip:$web_port"
            return 0
        else
            log_warning "컨테이너 연결 테스트 실패: $vm_ip:$web_port"
            return 1
        fi
    fi
}

# 프록시 규칙 동작 검증
verify_proxy_rule() {
    local user_id="$1"
    local vm_ip="$2"
    local web_port="$3"
    local max_attempts=30
    
    for ((i=1; i<=max_attempts; i++)); do
        if curl -s --connect-timeout 3 --max-time 10 "http://localhost/$user_id" >/dev/null 2>&1; then
            log_info "프록시 규칙 검증 성공: /localhost/$user_id (시도 $i/$max_attempts)"
            return 0
        fi
        
        if [[ $i -lt $max_attempts ]]; then
            sleep 1
        fi
    done
    
    log_warning "프록시 규칙 검증 실패: /localhost/$user_id ($max_attempts회 시도)"
    return 1
}

# 설정 자동 수정
auto_fix_config() {
    local user_id="$1"
    local vm_ip="$2"
    local web_port="$3"
    
    log_info "설정 자동 수정 시작: 사용자 $user_id"
    
    # 실제 컨테이너 정보 재조회
    local actual_ip
    local actual_port
    
    if command -v docker >/dev/null 2>&1; then
        # Docker 컨테이너에서 실제 IP 조회
        local container_name="webhost-vm-${user_id}"
        actual_ip=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$container_name" 2>/dev/null)
        
        if [[ -n "$actual_ip" && "$actual_ip" != "$vm_ip" ]]; then
            log_info "실제 컨테이너 IP 발견: $actual_ip (기존: $vm_ip)"
            
            # 설정 파일에서 IP 주소 수정
            local config_file="$HOSTING_DIR/${user_id}.conf"
            if [[ -f "$config_file" ]]; then
                sed -i "s|proxy_pass http://$vm_ip:|proxy_pass http://$actual_ip:|g" "$config_file"
                log_info "설정 파일 IP 주소 수정: $vm_ip -> $actual_ip"
                
                # nginx 리로드
                if systemctl reload nginx 2>/dev/null; then
                    log_info "nginx 리로드 완료"
                    
                    # 수정 후 재검증
                    sleep 3
                    if verify_proxy_rule "$user_id" "$actual_ip" "$web_port"; then
                        log_success "자동 수정 후 검증 성공: 사용자 $user_id"
                        return 0
                    fi
                fi
            fi
        fi
    fi
    
    log_error "설정 자동 수정 실패: 사용자 $user_id"
    return 1
}

# 사용자 호스팅 설정 제거
remove_user_config() {
    local user_id="$1"
    
    if [[ -z "$user_id" ]]; then
        log_error "사용자 ID가 필요합니다"
        return 1
    fi
    
    local config_file="$HOSTING_DIR/${user_id}.conf"
    
    if [[ ! -f "$config_file" ]]; then
        log_warning "사용자 $user_id의 설정 파일이 존재하지 않습니다"
        return 1
    fi
    
    log_info "사용자 $user_id 호스팅 설정 제거 중..."
    
    if [[ "$DRY_RUN" == false ]]; then
        rm -f "$config_file"
        rm -f "$LOG_DIR/hosting_${user_id}.access.log" 2>/dev/null || true
        
        log_success "사용자 $user_id 설정 제거 완료"
    else
        log_info "[DRY RUN] 다음 파일이 제거될 예정: $config_file"
    fi
}

# 등록된 사용자 목록
list_users() {
    log_info "등록된 호스팅 사용자 목록:"
    
    if [[ -d "$HOSTING_DIR" ]]; then
        local count=0
        for config_file in "$HOSTING_DIR"/*.conf; do
            if [[ -f "$config_file" ]]; then
                local user_id=$(basename "$config_file" .conf)
                local vm_id=$(grep "# VM ID:" "$config_file" 2>/dev/null | cut -d: -f2 | xargs || echo "N/A")
                echo "  • 사용자 ID: $user_id (VM: $vm_id)"
                ((count++))
            fi
        done
        
        if [[ $count -eq 0 ]]; then
            echo "  등록된 사용자가 없습니다."
        else
            echo "  총 $count명의 사용자가 등록되어 있습니다."
        fi
    else
        echo "  호스팅 디렉토리가 존재하지 않습니다."
    fi
}

# Nginx 설정 검증
validate_config() {
    log_info "Nginx 설정 검증 중..."
    
    if nginx -t 2>/dev/null; then
        log_success "Nginx 설정이 올바릅니다"
        return 0
    else
        log_error "Nginx 설정에 오류가 있습니다:"
        nginx -t
        return 1
    fi
}

# Nginx 설정 리로드
reload_nginx() {
    log_info "Nginx 설정 리로드 중..."
    
    if validate_config; then
        if [[ "$DRY_RUN" == false ]]; then
            systemctl reload nginx
            log_success "Nginx 리로드 완료"
        else
            log_info "[DRY RUN] Nginx가 리로드될 예정입니다"
        fi
    else
        log_error "설정 검증 실패로 리로드를 취소합니다"
        return 1
    fi
}

# Nginx 상태 확인
check_status() {
    log_info "Nginx 상태 확인:"
    
    if systemctl is-active --quiet nginx; then
        log_success "Nginx 서비스: 실행 중"
    else
        log_error "Nginx 서비스: 중지됨"
    fi
    
    echo ""
    echo "포트 사용 현황:"
    netstat -tlnp 2>/dev/null | grep -E ':(80|443|[0-9]{4,5})\s' | head -10
}

# 설정 파일 정리
cleanup_configs() {
    log_info "중복/불필요한 설정 파일 정리 중..."
    
    create_backup
    
    local cleaned=0
    
    # 기존 분산된 nginx 설정 파일들 제거
    local old_configs=(
        "../nginx-configs/proxy.conf"
        "../backend/nginx-configs"
    )
    
    for old_config in "${old_configs[@]}"; do
        if [[ -e "$old_config" && "$DRY_RUN" == false ]]; then
            log_warning "제거 중: $old_config"
            rm -rf "$old_config"
            ((cleaned++))
        elif [[ -e "$old_config" ]]; then
            log_info "[DRY RUN] 제거될 예정: $old_config"
            ((cleaned++))
        fi
    done
    
    if [[ $cleaned -gt 0 ]]; then
        log_success "$cleaned개의 파일/디렉토리를 정리했습니다"
    else
        log_info "정리할 파일이 없습니다"
    fi
}

# 기존 설정 마이그레이션
migrate_configs() {
    log_info "기존 설정을 새 구조로 마이그레이션 중..."
    
    create_backup
    
    # 기존 backend/nginx-configs의 사용자 설정들을 새 구조로 이동
    local old_dir="../backend/nginx-configs"
    local migrated=0
    
    if [[ -d "$old_dir" ]]; then
        for old_config in "$old_dir"/*.conf; do
            if [[ -f "$old_config" && $(basename "$old_config") =~ ^[0-9]+\.conf$ ]]; then
                local user_id=$(basename "$old_config" .conf)
                
                # 기존 설정에서 정보 추출
                local vm_ip=$(grep -o 'proxy_pass http://[^:]*' "$old_config" | cut -d'/' -f3 || echo "127.0.0.1")
                local web_port=$(grep -o 'proxy_pass http://[^:]*:[0-9]*' "$old_config" | cut -d':' -f3 || echo "8${user_id}00")
                local ssh_port=$(grep -o 'SSH 접속: ssh -p [0-9]*' "$old_config" | grep -o '[0-9]*' || echo "100${user_id}")
                local vm_id=$(grep -o '# VM ID: [^[:space:]]*' "$old_config" | cut -d' ' -f3 || echo "vm-${user_id}")
                
                log_info "마이그레이션: 사용자 $user_id (VM: $vm_id)"
                
                if [[ "$DRY_RUN" == false ]]; then
                    VM_ID="$vm_id" VM_IP="$vm_ip" WEB_PORT="$web_port" SSH_PORT="$ssh_port" \
                        add_user_config "$user_id"
                else
                    log_info "[DRY RUN] 사용자 $user_id 설정이 마이그레이션될 예정"
                fi
                
                ((migrated++))
            fi
        done
    fi
    
    if [[ $migrated -gt 0 ]]; then
        log_success "$migrated개의 사용자 설정을 마이그레이션했습니다"
    else
        log_info "마이그레이션할 설정이 없습니다"
    fi
}

# 메인 실행 로직
main() {
    # 명령어가 지정되지 않은 경우
    if [[ -z "$COMMAND" ]]; then
        log_error "명령어가 필요합니다"
        print_help
        exit 1
    fi
    
    # 요구사항 검증
    check_requirements || exit 1
    
    # 명령어별 실행
    case "$COMMAND" in
        init)
            init_nginx_config
            ;;
        add-user)
            add_user_config "$USER_ID"
            ;;
        remove-user)
            remove_user_config "$USER_ID"
            ;;
        update-user)
            remove_user_config "$USER_ID"
            add_user_config "$USER_ID"
            ;;
        list-users)
            list_users
            ;;
        validate)
            validate_config
            ;;
        reload)
            reload_nginx
            ;;
        status)
            check_status
            ;;
        cleanup)
            cleanup_configs
            ;;
        migrate)
            migrate_configs
            ;;
        *)
            log_error "알 수 없는 명령어: $COMMAND"
            print_help
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@" 