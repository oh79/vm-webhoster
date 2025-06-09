# 🔒 보안 주의사항 및 프로덕션 배포 가이드

## ⚠️ 중요: 프로덕션 배포 전 필수 체크사항

### 1. 시크릿 키 변경 (매우 중요)

**현재 개발용 설정 (절대 프로덕션 사용 금지):**

```python
# backend/app/core/config.py
SECRET_KEY: str = Field(
    default="dev-secret-key-change-this-in-production",  # ❌ 개발용
    description="JWT 토큰 서명용 비밀 키"
)
```

**프로덕션 배포 시 반드시 변경:**

```bash
# 1. 강력한 시크릿 키 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. 환경변수로 설정
export SECRET_KEY="your-super-secure-random-key-here"

# 3. 또는 .env 파일 사용
echo "SECRET_KEY=your-super-secure-random-key-here" > .env
```

### 2. Docker Compose 보안 설정

**현재 개발용 설정 (보안 취약):**

```yaml
# docker-compose.yml
environment:
  - SECRET_KEY=your-super-secret-key-change-this-in-production  # ❌ 하드코딩
  - DATABASE_URL=postgresql://webhoster_user:webhoster_pass@db:5432/webhoster_db  # ❌ 약한 비밀번호
```

**프로덕션용 설정:**

```yaml
# docker-compose.prod.yml
environment:
  - SECRET_KEY=${SECRET_KEY}  # 환경변수 사용
  - DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@db:5432/${DB_NAME}
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # 강력한 비밀번호
```

### 3. 데이터베이스 보안

```bash
# 강력한 데이터베이스 비밀번호 생성
python -c "import secrets; print(secrets.token_urlsafe(16))"

# 환경변수 설정
export POSTGRES_PASSWORD="generated-strong-password"
export DB_USER="webhoster_prod_user"
export DB_NAME="webhoster_production"
```

### 4. 프로덕션 환경변수 템플릿

**`.env.production.example` 파일 생성:**

```bash
# JWT 설정
SECRET_KEY=your-super-secure-jwt-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost/dbname
POSTGRES_USER=production_user
POSTGRES_PASSWORD=super_secure_password
POSTGRES_DB=webhoster_production

# 서버 설정
HOST=0.0.0.0
PORT=8000
ALLOWED_HOSTS=["yourdomain.com","www.yourdomain.com"]

# 도메인 설정
SERVICE_DOMAIN=yourdomain.com

# VM 관리 (실제 경로로 변경)
VM_IMAGE_PATH=/var/lib/libvirt/images
VM_TEMPLATE_IMAGE=ubuntu-20.04-server-cloudimg-amd64.img

# Nginx 설정
NGINX_CONFIG_PATH=/etc/nginx/sites-available/hosting

# SSH 포트 범위
SSH_PORT_RANGE_START=10000
SSH_PORT_RANGE_END=20000
```

## 🚫 절대 커밋하면 안되는 파일들

gitignore에 이미 추가되었지만, 특히 주의해야 할 항목들:

```
# 시크릿 키 및 인증서
*.key
*.pem
*.crt
*.p12
*.pfx

# 환경변수 파일
.env
.env.production
.env.local
production.env

# SSH 키
id_rsa
id_rsa.pub
authorized_keys

# 데이터베이스 파일
*.db
*.sqlite3
webhoster_dev.db

# 백업 파일
*.backup
*.dump
*.sql.gz
```

## 🔐 프로덕션 배포 체크리스트

### 배포 전 필수 확인사항

- [ ] **SECRET_KEY 변경** - 개발용 키를 강력한 프로덕션 키로 변경
- [ ] **데이터베이스 비밀번호 변경** - 기본 비밀번호 변경
- [ ] **ALLOWED_HOSTS 설정** - 실제 도메인으로 제한
- [ ] **DEBUG 모드 비활성화** - 프로덕션에서는 DEBUG=False
- [ ] **HTTPS 설정** - SSL/TLS 인증서 적용
- [ ] **방화벽 설정** - 필요한 포트만 개방
- [ ] **로그 레벨 조정** - 민감한 정보 로깅 방지
- [ ] **백업 전략 수립** - 데이터베이스 백업 계획

### 보안 헤더 설정

```python
# FastAPI 보안 헤더 설정
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

### 환경변수 관리

```bash
# 프로덕션 환경변수 설정 스크립트
#!/bin/bash

# .env.production 파일에서 환경변수 로드
set -a
source .env.production
set +a

# Docker 컨테이너 실행
docker-compose -f docker-compose.prod.yml up -d
```

## 🛡️ 보안 모니터링

### 로그 모니터링 항목

- 실패한 로그인 시도
- 무차별 대입 공격 탐지
- 비정상적인 API 호출 패턴
- JWT 토큰 위조 시도
- 권한 상승 시도

### 정기 보안 점검

- [ ] 의존성 취약점 스캔 (`pip audit`, `npm audit`)
- [ ] 시크릿 키 순환 (정기적으로 변경)
- [ ] 액세스 로그 검토
- [ ] 사용자 권한 검토
- [ ] 백업 파일 보안 상태 확인

## 📞 보안 이슈 발생 시 대응

1. **즉시 조치**
   - 해당 서비스 중단
   - 관련 계정 비활성화
   - 시크릿 키 재생성

2. **조사 및 복구**
   - 로그 분석
   - 영향 범위 파악
   - 보안 패치 적용

3. **사후 관리**
   - 보안 강화 조치
   - 모니터링 강화
   - 문서화 및 공유

---

**⚠️ 중요: 이 파일도 민감한 정보가 포함될 수 있으니, 실제 프로덕션 설정 값은 별도 관리하세요.** 