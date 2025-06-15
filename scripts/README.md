# 🚀 VM 웹호스터 스크립트 가이드

## 📋 스크립트 목록

### 1. 원클릭 설치 스크립트
- **00-run-all.sh**: 전체 시스템 자동 설치 및 설정
- **test-results-generator.sh**: 테스트 결과 자동 생성 (part4 문서용)

### 2. 단계별 설치 스크립트
- **01-system-setup.sh**: 시스템 초기 설정
- **02-project-setup.sh**: 프로젝트 환경 설정
- **03-dependencies.sh**: 의존성 설치
- **04-database-init.sh**: 데이터베이스 초기화
- **05-network-setup.sh**: 네트워크 및 방화벽 설정
- **06-start-services.sh**: 서비스 시작
- **07-test-services.sh**: 서비스 테스트

### 3. 관리 및 유지보수 스크립트
- **debug-services.sh**: 서비스 상태 진단
- **start-all.sh**: 모든 서비스 시작
- **stop-all.sh**: 모든 서비스 중지
- **nginx-config-manager.sh**: Nginx 설정 관리

---

## 🎯 주요 사용법

### 완전 자동 설치 (권장)

```bash
# 원클릭 설치 - 모든 환경 자동 구축
./scripts/00-run-all.sh
```

### 테스트 결과 생성 (part4 문서용)

```bash
# 테스트 결과 자동 생성 및 저장
./scripts/test-results-generator.sh

# 생성된 결과 확인
ls -la test-results/
cat test-results/00-test-summary.txt
```

### 문제 해결

```bash
# 서비스 상태 진단
./scripts/debug-services.sh

# 특정 단계 재실행
./scripts/04-database-init.sh

# 모든 서비스 재시작
./scripts/stop-all.sh && ./scripts/start-all.sh
```

---

## 📸 스크린샷 캡처 가이드

part4 문서에 필요한 스크린샷을 캡처하려면:

1. **테스트 결과 생성**
   ```bash
   ./scripts/test-results-generator.sh
   ```

2. **각 결과 파일 출력**
   ```bash
   cat test-results/01-system-info.txt
   cat test-results/02-service-status.txt
   cat test-results/03-api-tests.txt
   cat test-results/04-database-tests.txt
   cat test-results/05-performance-tests.txt
   ```

3. **스크린샷 가이드 확인**
   ```bash
   cat test-results/screenshot-guide.md
   ```

---

## ⚠️ 중요 사항

- **권한**: 모든 스크립트는 sudo 권한이 있는 일반 사용자로 실행
- **순서**: 00-run-all.sh 실행 후 test-results-generator.sh 실행 권장
- **환경**: Ubuntu 22.04 LTS 환경에서 테스트됨
- **시간**: 전체 설치는 15-25분, 테스트 생성은 2-3분 소요

---

## 🔧 트러블슈팅

### 일반적인 문제

1. **권한 오류**
   ```bash
   chmod +x scripts/*.sh
   sudo chown -R $USER:$USER ~/vm-webhoster
   ```

2. **포트 충돌**
   ```bash
   sudo fuser -k 8000/tcp 3000/tcp 80/tcp
   ```

3. **서비스 재시작**
   ```bash
   ./scripts/stop-all.sh
   sleep 5
   ./scripts/00-run-all.sh
   ```

### 로그 확인

```bash
# 설치 로그
tail -f logs/install.log

# 단계별 로그
ls -la logs/step-*.log

# 테스트 실행 로그
cat test-results/test-execution.log
```

---

*모든 스크립트는 실제 Production 환경에서 테스트되었습니다.* 