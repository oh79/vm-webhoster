# 📸 스크린샷 캡처 가이드

이 가이드는 part4 문서에 포함할 스크린샷들을 캡처하는 방법을 안내합니다.

## 📋 캡처할 스크린샷 목록

### 1. 테스트 실행 시작 화면
```bash
./scripts/test-results-generator.sh
```
**캡처 시점**: 스크립트 시작 시 배너 화면

### 2. 시스템 정보 출력
```bash
cat test-results/01-system-info.txt
```
**캡처 시점**: 시스템 정보 전체 화면

### 3. 서비스 상태 확인 결과
```bash
cat test-results/02-service-status.txt
```
**캡처 시점**: 서비스 상태 출력 화면

### 4. API 테스트 결과
```bash
cat test-results/03-api-tests.txt
```
**캡처 시점**: API 테스트 결과 전체 화면

### 5. 데이터베이스 연결 테스트
```bash
cat test-results/04-database-tests.txt
```
**캡처 시점**: 데이터베이스 테스트 결과 화면

### 6. 성능 테스트 결과
```bash
cat test-results/05-performance-tests.txt
```
**캡처 시점**: 성능 테스트 결과 화면

### 7. 전체 요약 화면
```bash
cat test-results/00-test-summary.txt
```
**캡처 시점**: 전체 테스트 요약 화면

### 8. 실시간 API 테스트
```bash
# 브라우저에서 접속하여 캡처
http://localhost:8000/docs
```
**캡처 시점**: FastAPI 문서 페이지

### 9. 웹 인터페이스
```bash
# 브라우저에서 접속하여 캡처
http://localhost:3000
```
**캡처 시점**: 프론트엔드 대시보드 화면

### 10. 최종 성공 메시지
```bash
echo "✅ 모든 테스트 완료!"
```
**캡처 시점**: 테스트 완료 후 터미널 화면

## 📝 캡처 팁

1. **터미널 크기**: 80x24 또는 그 이상으로 설정
2. **폰트 크기**: 가독성을 위해 적절한 크기로 조정
3. **색상**: 컬러 출력이 보이도록 설정
4. **전체 화면**: 각 명령어의 전체 출력이 보이도록 캡처

## 🎯 part4 문서에서 사용할 위치

각 스크린샷은 part4 문서의 해당 섹션에 다음 형식으로 표시:
**📸 스크린샷 첨부 위치: [SCREENSHOT-테스트명] 설명**

