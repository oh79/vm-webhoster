# 📋 웹 호스팅 서비스 설치 가이드

SSH로 VM에 접속하여 웹 호스팅 서비스를 처음부터 설치하고 테스트하는 완전 가이드입니다.

## 🚀 빠른 시작 (순서대로 실행)

```bash
# VM에 SSH 접속 후 아래 명령어들을 순서대로 실행하세요

# 1단계: 시스템 초기 설정
./scripts/01-system-setup.sh

# 2단계: 프로젝트 다운로드 및 기본 설정  
./scripts/02-project-setup.sh

# 3단계: 의존성 설치
./scripts/03-dependencies.sh

# 4단계: 데이터베이스 초기화
./scripts/04-database-init.sh

# 5단계: 네트워크 및 방화벽 설정
./scripts/05-network-setup.sh

# 6단계: 서비스 시작
./scripts/06-start-services.sh

# 7단계: 서비스 테스트
./scripts/07-test-services.sh
```

## 📖 각 단계별 상세 설명

### 1️⃣ 시스템 초기 설정 (`01-system-setup.sh`)
- 시스템 패키지 업데이트
- 필수 패키지 설치 (curl, git, python3, nodejs 등)
- Docker 설치 및 설정
- PostgreSQL, Redis 설치
- 기본 방화벽 설정

**예상 소요 시간**: 10-15분

### 2️⃣ 프로젝트 설정 (`02-project-setup.sh`)
- GitHub에서 프로젝트 클론 (또는 기존 프로젝트 업데이트)
- 환경변수 파일 생성 (.env)
- VM IP 주소 자동 감지 및 설정
- 필수 디렉토리 생성
- 데이터베이스 사용자 생성

**예상 소요 시간**: 2-3분

### 3️⃣ 의존성 설치 (`03-dependencies.sh`)
- Python 가상환경 생성
- 백엔드 Python 의존성 설치
- 프론트엔드 Node.js 의존성 설치
- 전역 개발 도구 설치
- 서비스 상태 확인

**예상 소요 시간**: 5-10분

### 4️⃣ 데이터베이스 초기화 (`04-database-init.sh`)
- 데이터베이스 연결 테스트
- Alembic 마이그레이션 실행
- 초기 데이터 삽입
- 관리자 계정 생성 (admin@example.com)
- 테이블 생성 확인

**예상 소요 시간**: 2-3분

### 5️⃣ 네트워크 설정 (`05-network-setup.sh`)
- 방화벽 포트 설정 (80, 443, 3000, 8000 등)
- Nginx 설치 및 프록시 설정
- IP 포워딩 활성화
- 포트 사용 현황 확인
- 외부 접근 설정 안내

**예상 소요 시간**: 3-5분

### 6️⃣ 서비스 시작 (`06-start-services.sh`)
- 기존 프로세스 정리
- 인프라 서비스 상태 확인 및 시작
- FastAPI 백엔드 서버 시작 (포트 8000)
- Next.js 프론트엔드 서버 시작 (포트 3000)
- 서비스 준비 상태 확인
- 접속 정보 표시

**예상 소요 시간**: 2-3분

### 7️⃣ 서비스 테스트 (`07-test-services.sh`)
- 기본 연결성 테스트
- 인프라 서비스 테스트
- API 기능 테스트 (회원가입, 로그인, 호스팅 생성)
- 프론트엔드 테스트
- Nginx 프록시 테스트
- Docker 컨테이너 테스트
- 성능 및 리소스 테스트
- 종합 결과 리포트

**예상 소요 시간**: 3-5분

## 🛠️ 추가 유틸리티 스크립트

### 관리 및 디버깅
- `debug-services.sh` - 서비스 상태 디버깅
- `stop-all.sh` - 모든 서비스 중지
- `get-vm-ip.sh` - VM IP 주소 확인

### 호스팅 관리
- `apply_nginx_config.sh` - Nginx 설정 적용
- `remove_nginx_config.sh` - Nginx 설정 제거
- `update_webhosting_config.sh` - 웹호스팅 설정 업데이트

### 네트워크 및 포트
- `fix-network.sh` - 네트워크 문제 해결
- `manage-ports.sh` - 포트 관리
- `test-connection.sh` - 연결 테스트

## 🔧 문제 해결

### 일반적인 문제들

#### 1. Docker 권한 오류
```bash
sudo usermod -aG docker $USER
newgrp docker
# 또는 재로그인
```

#### 2. 포트 충돌
```bash
# 포트 사용 확인
sudo ss -tlnp | grep :8000
sudo ss -tlnp | grep :3000

# 프로세스 종료
sudo pkill -f uvicorn
sudo pkill -f "node.*next"
```

#### 3. 데이터베이스 연결 오류
```bash
# PostgreSQL 서비스 확인
sudo systemctl status postgresql
sudo systemctl start postgresql

# 연결 테스트
psql postgresql://webhoster_user:webhoster_pass@localhost:5432/webhoster_db -c "SELECT 1;"
```

#### 4. 방화벽 문제
```bash
# 방화벽 상태 확인
sudo ufw status

# 포트 허용
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 80/tcp
```

### 로그 확인
```bash
# 서비스 로그
tail -f logs/backend.log
tail -f logs/frontend.log

# 시스템 로그
sudo journalctl -u postgresql
sudo journalctl -u nginx
sudo journalctl -u docker
```

## 🌐 접속 정보

설정 완료 후 다음 URL로 접속 가능합니다:

- **메인 사이트**: `http://localhost` (Nginx 프록시)
- **백엔드 API**: `http://localhost:8000/docs` (FastAPI 문서)
- **프론트엔드**: `http://localhost:3000` (Next.js 개발 서버)

### 외부 접근 (VM 환경)
- **VM 내부 IP**: `http://VM_IP:80`
- **백엔드**: `http://VM_IP:8000/docs`
- **프론트엔드**: `http://VM_IP:3000`

## 🔐 기본 계정

- **관리자**: admin@example.com / admin123
- **테스트 계정**: test@example.com / test123456

## 📞 추가 도움

### 전체 재설치
```bash
# 모든 서비스 중지
./scripts/stop-all.sh

# 데이터 초기화 (주의!)
sudo rm -rf backend/vm-images/*
sudo rm -rf logs/*

# 1단계부터 다시 시작
./scripts/01-system-setup.sh
```

### 개발 모드 지속 실행
```bash
# 백그라운드에서 지속 실행
nohup ./scripts/06-start-services.sh &

# 로그 모니터링
tail -f logs/*.log
```

---

**총 예상 설치 시간**: 25-40분
**필요 시스템 요구사항**: Ubuntu 22.04, 4GB RAM, 20GB 디스크 