# Nginx 설정 리팩토링 가이드

## 🎯 개요

이 문서는 웹 호스팅 서비스의 nginx 설정 파일들을 체계적으로 리팩토링한 내용을 설명합니다.

## 📋 리팩토링 전/후 비교

### Before (이전 구조)
```
vm-webhoster/
├── nginx/nginx.conf                 # 메인 설정 (중복된 내용)
├── nginx-configs/proxy.conf         # 프록시 설정 (중복)
├── backend/nginx-configs/           # 사용자별 설정들 (분산)
│   ├── 1.conf, 2.conf, ...         # 개별 사용자 설정
│   ├── webhosting.conf              # 메인 호스팅 설정
│   └── backup/                      # 백업 파일들
└── scripts/                         # 관리 스크립트들 (분산)
    ├── apply_nginx_config.sh
    └── remove_nginx_config.sh
```

**문제점:**
- 중복된 메인 페이지 설정 (3곳에 중복)
- 일관성 없는 포트 및 IP 설정
- 분산된 관리 스크립트
- 설정 파일 관리의 복잡성

### After (리팩토링 후 구조)
```
vm-webhoster/
├── nginx/                           # 통합된 nginx 설정
│   ├── nginx.conf                   # 메인 설정 (모듈화)
│   ├── conf.d/                      # 모듈별 설정
│   │   ├── upstream.conf            # 업스트림 정의
│   │   ├── security.conf            # 보안 설정
│   │   └── compression.conf         # 압축 설정
│   ├── sites-available/             # 사이트 설정
│   │   ├── main.conf               # 메인 사이트 (통합)
│   │   └── hosting/                # 사용자별 호스팅
│   │       ├── 1.conf
│   │       ├── 2.conf
│   │       └── ...
│   └── templates/                   # 템플릿 파일
│       └── user-hosting.conf.j2     # 사용자 설정 템플릿
└── scripts/
    └── nginx-config-manager.sh      # 통합 관리 스크립트
```

**개선점:**
- 모듈화된 설정 구조
- 템플릿 기반 자동 생성
- 통합된 관리 스크립트
- 일관된 보안 및 성능 설정

## 🏗️ 새로운 구조 상세

### 1. 메인 nginx 설정 (`nginx/nginx.conf`)

**특징:**
- 모듈별 설정 include 방식
- 성능 최적화 설정
- 사용자별 로그 포맷 정의

```nginx
# 모듈별 설정 포함
include /etc/nginx/conf.d/*.conf;

# 사이트별 설정 포함  
include /etc/nginx/sites-available/*.conf;
include /etc/nginx/sites-available/hosting/*.conf;
```

### 2. 모듈별 설정 (`nginx/conf.d/`)

#### 업스트림 설정 (`upstream.conf`)
- 백엔드 API 서버 정의
- 프론트엔드 서버 정의
- Redis 백엔드 정의
- Keepalive 연결 최적화

#### 보안 설정 (`security.conf`)
- Rate limiting 설정
- 보안 헤더 정의
- 차단 규칙 설정
- CORS 설정

#### 압축 설정 (`compression.conf`)
- Gzip 압축 최적화
- 정적 파일 캐싱
- 성능 튜닝 설정

### 3. 메인 사이트 설정 (`nginx/sites-available/main.conf`)

**특징:**
- 통합된 메인 페이지 (중복 제거)
- API 프록시 설정
- 에러 페이지 정의
- 헬스체크 엔드포인트

**주요 기능:**
```nginx
# 메인 페이지 - 통합된 웹 호스팅 서비스 소개
location = / {
    return 200 '<!DOCTYPE html>...';
}

# API 프록시 (백엔드 서버로)
location /api/ {
    proxy_pass http://backend_api;
    # CORS 및 보안 설정
}

# 헬스체크
location /health {
    return 200 '{"status": "healthy"}';
}
```

### 4. 사용자 호스팅 템플릿 (`nginx/templates/user-hosting.conf.j2`)

**특징:**
- Jinja2 템플릿 엔진 사용
- 동적 사용자 설정 생성
- 에러 페이지 포함
- 상세한 로깅

**템플릿 변수:**
- `{{ user_id }}`: 사용자 ID
- `{{ vm_id }}`: VM ID
- `{{ vm_ip }}`: VM IP 주소
- `{{ web_port }}`: 웹 포트
- `{{ ssh_port }}`: SSH 포트

## 🛠️ 통합 관리 스크립트

### `nginx-config-manager.sh` 주요 기능

#### 1. 초기화
```bash
./nginx-config-manager.sh init
```
- nginx 디렉토리 구조 생성
- 기본 설정 파일 복사
- 권한 설정

#### 2. 사용자 추가
```bash
./nginx-config-manager.sh add-user 7 \
  --vm-id vm-abc123 \
  --vm-ip 192.168.122.100 \
  --web-port 8007 \
  --ssh-port 10007
```

#### 3. 사용자 제거
```bash
./nginx-config-manager.sh remove-user 7
```

#### 4. 설정 검증 및 리로드
```bash
./nginx-config-manager.sh validate
./nginx-config-manager.sh reload
```

#### 5. 상태 확인
```bash
./nginx-config-manager.sh status
./nginx-config-manager.sh list-users
```

#### 6. 정리 및 마이그레이션
```bash
./nginx-config-manager.sh cleanup --backup
./nginx-config-manager.sh migrate --backup
```

## 🔄 마이그레이션 프로세스

### 1. 기존 설정 백업
```bash
# 자동 백업 생성
./nginx-config-manager.sh migrate --backup
```

### 2. 새 구조로 변환
- 기존 `backend/nginx-configs/*.conf` 파일들을 분석
- 사용자 ID, VM 정보, 포트 정보 추출
- 새 템플릿을 사용하여 설정 재생성

### 3. 중복 파일 정리
```bash
# 이전 버전 설정 파일들 정리
./nginx-config-manager.sh cleanup --backup
```

### 4. 설정 검증
```bash
# nginx 설정 유효성 검증
./nginx-config-manager.sh validate
```

### 5. 서비스 리로드
```bash
# 새 설정 적용
./nginx-config-manager.sh reload
```

## 📊 개선된 백엔드 서비스

### `ProxyService` 클래스 업데이트

**주요 변경사항:**
- nginx 관리 스크립트 통합
- 템플릿 기반 설정 생성
- 자동 백업 및 롤백
- 상세한 에러 처리

**새로운 메서드:**
```python
# 프록시 규칙 관리
proxy_service.add_proxy_rule(user_id, vm_ip, ssh_port, web_port, vm_id)
proxy_service.remove_proxy_rule(user_id)
proxy_service.update_proxy_rule(user_id, vm_ip, ssh_port, web_port, vm_id)

# 정보 조회
proxy_service.get_proxy_info(user_id)
proxy_service.list_proxy_rules()
proxy_service.get_nginx_status()

# 관리 기능
proxy_service.validate_nginx_config()
proxy_service.cleanup_old_configs()
proxy_service.migrate_from_old_structure()
```

## 🎯 리팩토링 효과

### 1. 성능 개선
- **모듈화**: 설정 로딩 시간 단축
- **캐싱**: 정적 파일 캐시 최적화
- **압축**: Gzip 압축 개선
- **Keepalive**: 연결 재사용 최적화

### 2. 보안 강화
- **Rate Limiting**: API별 차등 제한
- **보안 헤더**: 일관된 보안 정책
- **CORS**: 적절한 CORS 설정
- **에러 처리**: 정보 노출 방지

### 3. 관리 효율성
- **자동화**: 수동 작업 최소화
- **템플릿**: 일관된 설정 생성
- **백업**: 자동 백업 시스템
- **검증**: 설정 유효성 자동 확인

### 4. 개발자 경험
- **통합 CLI**: 단일 명령어로 모든 작업
- **로깅**: 상세한 작업 로그
- **에러 메시지**: 명확한 오류 안내
- **문서화**: 완전한 사용 가이드

## 🚀 실제 사용 예시

### 전체 시스템 초기화
```bash
# 1. nginx 구조 초기화
./scripts/nginx-config-manager.sh init

# 2. 기존 설정 마이그레이션
./scripts/nginx-config-manager.sh migrate --backup

# 3. 이전 파일들 정리
./scripts/nginx-config-manager.sh cleanup --backup

# 4. 설정 검증 및 적용
./scripts/nginx-config-manager.sh validate
./scripts/nginx-config-manager.sh reload
```

### 새 사용자 호스팅 생성
```bash
# 호스팅 API 호출로 자동 생성되거나 수동 생성 가능
./scripts/nginx-config-manager.sh add-user 10 \
  --vm-id vm-new123 \
  --vm-ip 192.168.122.110 \
  --web-port 8010 \
  --ssh-port 10010
```

### 상태 모니터링
```bash
# 시스템 상태 확인
./scripts/nginx-config-manager.sh status

# 등록된 사용자 목록
./scripts/nginx-config-manager.sh list-users

# nginx 설정 검증
./scripts/nginx-config-manager.sh validate
```

## 📝 주의사항

### 1. 백업
- 모든 변경 작업 전에 `--backup` 옵션 사용 권장
- 백업 파일은 `/tmp/nginx-backup-YYYYMMDD-HHMMSS/` 에 저장

### 2. 권한
- nginx 관리 스크립트는 sudo 권한이 필요할 수 있음
- 스크립트 실행 권한 확인: `chmod +x nginx-config-manager.sh`

### 3. 종속성
- Python 3 및 Jinja2 라이브러리 필요
- nginx 서비스가 설치되어 있어야 함

### 4. 테스트
- 프로덕션 적용 전 개발 환경에서 충분한 테스트 필요
- `--dry-run` 옵션으로 미리보기 가능

## 🔮 향후 개선 계획

### 1. 고급 기능
- SSL/TLS 인증서 자동 관리
- 로드 밸런싱 설정
- 웹소켓 프록시 최적화

### 2. 모니터링
- nginx 메트릭 수집
- 사용자별 트래픽 분석
- 자동 알림 시스템

### 3. 확장성
- Kubernetes 환경 지원
- 다중 서버 관리
- CDN 통합

이 리팩토링을 통해 nginx 설정 관리가 훨씬 체계적이고 안정적으로 개선되었습니다. 🎉 