# 웹 호스팅 서비스 TODO 리스트

## 📊 현재 구현 상태 (2024-01-XX 기준)

### ✅ 구현 완료 (약 80%)
- 사용자 인증 시스템 (회원가입/로그인/JWT)
- 호스팅 관리 API (생성/조회/삭제)
- VM 관리 서비스 (KVM/QEMU 기반)
- 데이터베이스 설계 및 마이그레이션
- 프론트엔드 UI (Next.js 14)
- 기본 에러 처리 및 로깅

### ❌ 미구현 (약 20% - 핵심 기능)
- **Nginx 프록시 서비스** (가장 중요)
- VM 내부 웹서버 자동 설치
- 포트 포워딩 설정
- 실제 서비스 배포 테스트

---

## 🔥 최우선 작업 항목 (프로젝트 완성을 위한 필수)

### 1. Nginx 프록시 서비스 구현
**파일**: `backend/app/services/proxy_service.py`
- [ ] ProxyService 클래스 생성
- [ ] `add_proxy_rule()` - 웹 포트 포워딩 (`/<user_id>` → `VM:80`)
- [ ] `add_ssh_forwarding()` - SSH 포트 포워딩 (`:<random_port>` → `VM:22`)
- [ ] `remove_proxy_rule()` - 프록시 규칙 삭제
- [ ] `reload_nginx()` - Nginx 설정 리로드

### 2. Nginx 설정 템플릿 생성
**파일**: `backend/templates/nginx.conf.j2`
- [ ] location 블록 템플릿
- [ ] proxy_pass 설정
- [ ] 헤더 전달 설정
- [ ] 에러 페이지 설정

### 3. VM 웹서버 자동 설치
**파일**: `backend/app/services/vm_service.py` 수정
- [ ] cloud-init 설정 추가
- [ ] Nginx 자동 설치 스크립트
- [ ] 기본 웹 페이지 생성 (`/var/www/html/index.html`)
- [ ] SSH 사용자 설정

### 4. 호스팅 서비스와 프록시 연동
**파일**: `backend/app/services/hosting_service.py` 수정
- [ ] VM 생성 시 프록시 규칙 자동 추가
- [ ] VM 삭제 시 프록시 규칙 자동 제거
- [ ] 프록시 실패 시 롤백 처리

---

## 🔶 중요 작업 항목

### 5. Docker Compose Nginx 서비스 활성화
**파일**: `docker-compose.yml` 수정
- [ ] Nginx 컨테이너 설정 활성화
- [ ] 볼륨 마운트 (설정 파일, 로그)
- [ ] 네트워크 설정
- [ ] 포트 매핑

### 6. 실제 Nginx 설정 디렉토리 생성
**디렉토리**: `nginx/`
- [ ] `nginx/nginx.conf` - 메인 설정
- [ ] `nginx/sites/` - 호스팅별 설정 저장소
- [ ] `nginx/ssl/` - SSL 인증서 (향후)

### 7. 프록시 관리 API 추가
**파일**: `backend/app/api/endpoints/hosting.py` 수정
- [ ] `GET /host/proxy-info` - 프록시 상태 확인
- [ ] `POST /host/reload-proxy` - 프록시 수동 리로드
- [ ] `GET /host/access-urls` - 접속 URL 정보

### 8. VM 상태 실시간 동기화
**파일**: `backend/app/services/vm_service.py` 수정
- [ ] VM 상태 변경 감지
- [ ] DB 상태 자동 업데이트
- [ ] 상태 불일치 복구 로직

---

## 🔷 개선 작업 항목

### 9. 테스트 구현
**디렉토리**: `backend/tests/`
- [ ] `test_proxy_service.py` - 프록시 서비스 테스트
- [ ] `test_vm_integration.py` - VM 생성/삭제 통합 테스트
- [ ] `test_hosting_flow.py` - 전체 플로우 테스트

### 10. 에러 처리 강화
- [ ] VM 생성 실패 시 자동 롤백
- [ ] 프록시 설정 실패 시 복구
- [ ] 네트워크 오류 재시도 로직
- [ ] 디스크 공간 부족 처리

### 11. 성능 최적화
- [ ] VM 생성 백그라운드 작업 개선
- [ ] 데이터베이스 쿼리 최적화
- [ ] 캐싱 전략 도입
- [ ] 연결 풀링 설정

### 12. 보안 강화
- [ ] VM 네트워크 격리
- [ ] 포트 스캔 방지
- [ ] Rate limiting 구현
- [ ] SSL/TLS 지원

---

## 🚀 배포 준비 작업

### 13. 프로덕션 설정
- [ ] 환경변수 분리 (`.env.production`)
- [ ] 시크릿 키 생성 및 보안 설정
- [ ] 로그 레벨 조정
- [ ] 성능 모니터링 설정

### 14. 문서화
- [ ] API 문서 업데이트
- [ ] 배포 가이드 작성
- [ ] 트러블슈팅 가이드
- [ ] 사용자 매뉴얼

### 15. 모니터링 시스템
- [ ] VM 리소스 모니터링
- [ ] 서비스 상태 모니터링
- [ ] 로그 수집 및 분석
- [ ] 알림 시스템

---

## ⚠️ 알려진 이슈 및 제한사항

### 기술적 이슈
1. **VM IP 할당 대기 시간** - DHCP 리스 확인 로직 필요
2. **포트 충돌 방지** - 사용 중인 포트 체크 강화 필요
3. **VM 생성 시간** - 5분 이상 소요될 수 있음
4. **동시 VM 생성 제한** - 리소스 경합 발생 가능

### 보안 이슈
1. **VM 간 격리** - 네트워크 세그멘테이션 필요
2. **권한 관리** - sudo 권한 최소화 필요
3. **SSH 키 관리** - 사용자별 키 쌍 관리 필요

---

## 📅 작업 스케줄 제안

### Week 1: 핵심 기능 완성
- Day 1-2: Nginx 프록시 서비스 구현
- Day 3-4: VM 웹서버 자동 설치
- Day 5-7: 통합 테스트 및 버그 수정

### Week 2: 안정화 및 개선
- Day 1-3: Docker 환경 완성
- Day 4-5: 에러 처리 강화
- Day 6-7: 성능 최적화

### Week 3: 배포 준비
- Day 1-3: 보안 강화
- Day 4-5: 문서화
- Day 6-7: 프로덕션 배포 테스트

---

## 🎯 완성 기준

### 최소 동작 요구사항 (MVP)
- [x] 사용자 회원가입/로그인
- [x] 호스팅 생성/삭제 API
- [x] VM 자동 생성/삭제
- [ ] **웹 서비스 접속 가능** (`http://domain/<user_id>`)
- [ ] **SSH 접속 가능** (`ssh -p <port> user@domain`)

### 프로덕션 준비 완료 기준
- [ ] 모든 핵심 기능 동작
- [ ] 에러 처리 완료
- [ ] 보안 검토 완료
- [ ] 성능 테스트 통과
- [ ] 문서화 완료

---

## 📞 참고 자료

- [PRD.md](./PRD.md) - 프로젝트 요구사항 문서
- [cursor_step.md](./cursor_step.md) - 단계별 구현 가이드
- [SECURITY.md](./SECURITY.md) - 보안 가이드
- [README.md](./README.md) - 프로젝트 개요

---

**마지막 업데이트**: 2024-01-XX  
**다음 작업**: Nginx 프록시 서비스 구현부터 시작 