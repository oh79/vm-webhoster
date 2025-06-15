# 웹 호스팅 서비스 설치 스크립트 가이드

## 🚀 개요

이 스크립트들은 Ubuntu 환경에서 완전한 웹 호스팅 서비스를 자동으로 설치하고 설정합니다.
모든 VM 생성 도구와 관련 문제들이 자동으로 해결되도록 개선되었습니다.

## 📋 자동으로 해결되는 문제들

### ✅ VM 생성 환경
- Docker, KVM/QEMU, libvirt 완전 설치
- Python Jinja2 템플릿 엔진 설치
- Nginx 프록시 환경 구성
- VM 디렉토리 구조 자동 생성

### ✅ 권한 및 서비스 문제
- Docker 소켓 권한 자동 설정
- Nginx PID 파일 문제 자동 해결
- 사용자 그룹 권한 자동 추가

### ✅ 의존성 문제
- requests 모듈 자동 설치 및 검증
- 누락된 Python 패키지 자동 보완
- nginx-config-manager 자동 초기화

## 🛠️ 사용법

### 완전 자동 설치
```bash
./scripts/00-run-all.sh
```

### 개별 단계 실행
```bash
./scripts/01-system-setup.sh    # 시스템 및 VM 도구 설치
./scripts/02-project-setup.sh   # 프로젝트 설정
./scripts/03-dependencies.sh    # 의존성 설치 (requests 포함)
./scripts/04-database-init.sh   # 데이터베이스 초기화
./scripts/05-network-setup.sh   # 네트워크 설정
./scripts/06-start-services.sh  # 서비스 시작
./scripts/07-test-services.sh   # 테스트 및 검증
```

### 환경 검증
```bash
./scripts/check-vm-tools.sh     # VM 환경 검증 (96%+ 성공률 기대)
```

## 📊 예상 결과

설치 완료 후:
- 성공률: 95-100%
- VM 생성 도구: 완전 설치
- Nginx 프록시: 정상 작동
- Docker 권한: 자동 해결
- 웹 호스팅: 즉시 사용 가능

## 🎯 추가 개선사항

이 버전에서 새로 추가된 기능들:

1. **Docker 권한 자동 해결**
   - 소켓 권한 자동 설정
   - 그룹 권한 확실히 적용

2. **Nginx PID 파일 문제 해결**
   - 자동 재시작으로 PID 파일 복구
   - 리로드 테스트 자동 실행

3. **requests 모듈 보장**
   - requirements.txt에 추가
   - 설치 검증 자동 실행

4. **최종 환경 검증**
   - check-vm-tools.sh 자동 실행
   - 모든 구성 요소 상태 확인

## 🔧 문제 해결

설치 중 문제가 발생하면:

```bash
# 상세 로그 확인
tail -f logs/install.log
tail -f logs/step-*.log

# 서비스 상태 확인
sudo systemctl status nginx
sudo systemctl status docker
sudo systemctl status postgresql

# VM 환경 재검증
./scripts/check-vm-tools.sh

# 개별 단계 재실행
./scripts/01-system-setup.sh  # 시스템 문제 시
./scripts/03-dependencies.sh  # 의존성 문제 시
```

## 🌟 성공 확인

설치가 성공하면:
1. 웹사이트 접속: http://localhost:3000
2. "호스팅 생성" 버튼 클릭
3. VM 인스턴스 생성 성공
4. 프록시 규칙 정상 작동

## ⚡ 빠른 시작

```bash
# 1. 프로젝트 클론
git clone <repository>
cd vm-webhoster

# 2. 완전 자동 설치
./scripts/00-run-all.sh

# 3. 웹사이트 접속
# http://localhost:3000
```

이제 모든 VM 생성 관련 문제가 자동으로 해결됩니다! 🎉 