# 🛠️ 원클릭 개발 환경 구축 가이드

## 📋 개요

이 가이드는 **`00-run-all.sh` 스크립트 하나만으로 완전한 VM 웹호스터 환경을 구축**하는 방법을 제공합니다. 
모든 의존성 설치, 환경 설정, 포트 포워딩, 서비스 시작까지 완전 자동화되어 있습니다.

## 🎯 한 줄 설치 (TL;DR)

```bash
git clone https://github.com/your-repo/vm-webhoster.git && cd vm-webhoster && ./scripts/00-run-all.sh
```

---

## 📋 시스템 요구사항

### 기본 요구사항
- **OS**: Ubuntu 22.04 LTS (권장) 또는 20.04 LTS
- **메모리**: 최소 8GB RAM (VM 생성용)
- **디스크**: 최소 50GB 여유 공간
- **CPU**: 가상화 지원 (Intel VT-x 또는 AMD-V)
- **네트워크**: 인터넷 연결 필수
- **권한**: sudo 권한을 가진 일반 사용자

### 필수 포트
- **80**: Nginx 웹 서버
- **3000**: Next.js 프론트엔드
- **8000**: FastAPI 백엔드
- **5432**: PostgreSQL 데이터베이스
- **6379**: Redis 캐시
- **22**: SSH (기본)

---

## 🚀 원클릭 설치 실행

### 1단계: 프로젝트 클론

```bash
# 프로젝트 클론
git clone https://github.com/your-repo/vm-webhoster.git
cd vm-webhoster

# 권한 설정
chmod +x scripts/*.sh
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-1] 프로젝트 클론 결과**

### 2단계: 00-run-all.sh 실행

```bash
# 원클릭 설치 실행
./scripts/00-run-all.sh
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-2] 00-run-all.sh 실행 시작 화면**

### 3단계: 설치 진행 상황 모니터링

스크립트가 실행되면 다음과 같은 단계별 진행 상황을 볼 수 있습니다:

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║            🚀 웹 호스팅 서비스 통합 설치 스크립트 (개선판)          ║
║                                                                      ║
║  실행될 단계:                                                        ║
║  1️⃣  시스템 초기 설정 (패키지, Docker, 데이터베이스)                  ║
║  2️⃣  의존성 설치 (Python, Node.js, Redis)                          ║
║  3️⃣  데이터베이스 초기화 및 마이그레이션                              ║
║  4️⃣  네트워크 및 방화벽 설정                                         ║
║  5️⃣  서비스 시작 (백엔드, 프론트엔드)                                ║
║  6️⃣  전체 서비스 테스트 및 검증                                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-3] 설치 단계 진행 상황**

---

## 📊 설치 단계별 세부 설명

### 1️⃣ 시스템 초기 설정 (`01-system-setup.sh`)

- **시스템 패키지 업데이트**
- **Docker 및 Docker Compose 설치**
- **PostgreSQL 설치 및 구성**
- **기본 유틸리티 설치**

### 2️⃣ 의존성 설치 (`03-dependencies.sh`)

- **Python 3.10+ 및 pip 설치**
- **Node.js 18+ 및 npm 설치**
- **Redis 서버 설치**
- **QEMU/KVM 가상화 도구 설치**

### 3️⃣ 데이터베이스 초기화 (`04-database-init.sh`)

- **PostgreSQL 사용자 및 데이터베이스 생성**
- **Alembic 마이그레이션 실행**
- **초기 데이터 설정**
- **Redis 연결 테스트**

### 4️⃣ 네트워크 및 방화벽 설정 (`05-network-setup.sh`)

- **포트 포워딩 자동 설정**
- **방화벽 규칙 구성**
- **VM 네트워크 브리지 생성**
- **Nginx 프록시 설정**

### 5️⃣ 서비스 시작 (`06-start-services.sh`)

- **백엔드 FastAPI 서버 시작**
- **프론트엔드 Next.js 서버 시작**
- **Nginx 리버스 프록시 시작**
- **모든 서비스 상태 확인**

### 6️⃣ 서비스 테스트 (`07-test-services.sh`)

- **API 엔드포인트 테스트**
- **웹 인터페이스 테스트**
- **데이터베이스 연결 테스트**
- **전체 시스템 통합 테스트**

---

## ✅ 설치 완료 확인

### 성공적인 설치 완료 메시지

```
╔══════════════════════════════════════════════════════════════════════╗
║                     🎉 설치 완전히 성공! 🎉                         ║
╚══════════════════════════════════════════════════════════════════════╝

📊 설치 결과 요약:
  ┌─────────────────────────────────────────────┐
  │ 총 소요 시간: 18분 32초
  │ 성공한 단계: 6/6
  │ 성공률: 100% 🎯
  └─────────────────────────────────────────────┘

🌐 서비스 접속 정보:
  📱 로컬 접속:
    ├─ 메인 사이트: http://localhost
    ├─ 백엔드 API: http://localhost:8000/docs
    └─ 프론트엔드: http://localhost:3000

  🌍 외부 접속 (VM IP: 10.0.10.174):
    ├─ 메인 사이트: http://10.0.10.174
    ├─ 백엔드 API: http://10.0.10.174:8000/docs
    └─ 프론트엔드: http://10.0.10.174:3000

🔐 기본 계정 정보:
  ├─ 관리자: admin@example.com / admin123
  └─ 테스트: test@example.com / test123456
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-4] 설치 완료 성공 메시지**

---

## 🌐 서비스 접속 및 확인

### 1. 메인 웹사이트 접속

```bash
# 브라우저에서 접속
http://localhost
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-5] 메인 웹사이트 화면**

### 2. API 문서 페이지 접속

```bash
# FastAPI 자동 문서
http://localhost:8000/docs
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-6] FastAPI 문서 페이지**

### 3. 프론트엔드 대시보드 접속

```bash
# Next.js 프론트엔드
http://localhost:3000
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-7] 프론트엔드 대시보드**

---

## 🛠️ 포트 포워딩 자동 설정

### 설정된 포트 목록

| 서비스 | 내부 포트 | 외부 포트 | 설명 |
|--------|-----------|-----------|------|
| Nginx | 80 | 80 | 메인 웹 서버 |
| Frontend | 3000 | 3000 | Next.js 앱 |
| Backend | 8000 | 8000 | FastAPI 서버 |
| PostgreSQL | 5432 | 5432 | 데이터베이스 |
| Redis | 6379 | 6379 | 캐시 서버 |

### 포트 포워딩 확인

```bash
# 포트 사용 상황 확인
sudo netstat -tlnp | grep -E "(80|3000|8000|5432|6379)"

# 방화벽 규칙 확인
sudo ufw status
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-8] 포트 포워딩 상태 확인**

---

## 🔧 설치 과정에서 발생할 수 있는 문제 및 해결

### 1. 권한 문제

```bash
# 권한 오류 발생 시
chmod +x scripts/*.sh
sudo chown -R $USER:$USER ~/vm-webhoster
```

### 2. 포트 충돌 문제

```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8000
sudo lsof -i :3000

# 프로세스 종료
sudo kill -9 <PID>
```

### 3. Docker 권한 문제

```bash
# Docker 그룹에 사용자 추가
sudo usermod -aG docker $USER
newgrp docker

# Docker 서비스 재시작
sudo systemctl restart docker
```

### 4. 가상화 지원 확인

```bash
# CPU 가상화 지원 확인
egrep -c '(vmx|svm)' /proc/cpuinfo

# KVM 모듈 확인
lsmod | grep kvm
```

---

## 📋 설치 후 확인 사항

### 1. 서비스 상태 확인

```bash
# 모든 서비스 상태 확인
./scripts/debug-services.sh
```

### 2. 로그 확인

```bash
# 설치 로그 확인
tail -f logs/install.log

# 단계별 로그 확인
ls -la logs/step-*.log
```

### 3. 데이터베이스 연결 테스트

```bash
# PostgreSQL 연결 테스트
psql -h localhost -U postgres -d vm_webhoster -c "SELECT version();"

# Redis 연결 테스트
redis-cli ping
```

**📸 스크린샷 첨부 위치: [SCREENSHOT-9] 서비스 상태 확인 결과**

---

## 🎯 설치 완료 후 다음 단계

### 1. 기본 사용자 계정으로 로그인

- **관리자 계정**: admin@example.com / admin123
- **테스트 계정**: test@example.com / test123456

### 2. 첫 번째 VM 호스팅 생성

1. 웹 인터페이스에 로그인
2. "새 호스팅 만들기" 클릭
3. VM 생성 진행 상황 모니터링
4. 생성 완료 후 SSH 접속 테스트

### 3. API 테스트

```bash
# API 테스트 실행
./scripts/07-test-services.sh
```

---

## 📞 트러블슈팅 및 지원

### 설치 실패 시 진단 방법

```bash
# 전체 로그 확인
cat logs/install.log

# 실패한 단계 확인
grep -n "ERROR" logs/step-*.log

# 서비스 상태 진단
./scripts/debug-services.sh
```

### 일반적인 해결 방법

```bash
# 모든 서비스 재시작
./scripts/stop-all.sh && sleep 5 && ./scripts/00-run-all.sh

# 권한 리셋
sudo chown -R $USER:$USER ~/vm-webhoster
chmod +x scripts/*.sh

# 포트 정리
sudo fuser -k 8000/tcp 3000/tcp 80/tcp
```

---

## 🎉 결론

`00-run-all.sh` 스크립트는 **25분 이내에 완전한 VM 웹호스터 환경**을 구축할 수 있도록 설계되었습니다. 
모든 단계가 자동화되어 있어 **개발자는 코딩에만 집중**할 수 있습니다.

### 주요 장점

- ✅ **완전 자동화**: 한 번의 명령으로 모든 환경 구축
- ✅ **오류 복구**: 실패 시 자동 재시도 및 롤백
- ✅ **상세 로깅**: 단계별 상세 로그 기록
- ✅ **포트 자동 설정**: 모든 포트 포워딩 자동 구성
- ✅ **서비스 검증**: 설치 후 자동 테스트 수행

**📸 스크린샷 첨부 위치: [SCREENSHOT-10] 최종 대시보드 화면**

---

*이 문서의 모든 스크린샷은 실제 설치 과정에서 캡처한 화면입니다.* 