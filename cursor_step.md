# Cursor IDE 단계별 구현 프롬프트 (Python/FastAPI + Next.js)

## Phase 1: 프로젝트 초기 설정

### Prompt 1.1: 프로젝트 구조 생성
```
Ubuntu 22.04 LTS 환경에서 웹 호스팅 서비스를 위한 프로젝트 구조를 생성해주세요.

요구사항:
1. Python/FastAPI 기반 백엔드
2. Next.js 프론트엔드 (v0로 개발 예정)
3. PostgreSQL 데이터베이스
4. 다음 디렉토리 구조 생성:
   - /web-hosting-service
     - /backend
       - /app
         - /api
           - /endpoints
         - /core
         - /db
         - /models
         - /schemas
         - /services
         - /utils
       - /tests
       - /alembic (DB 마이그레이션)
       - requirements.txt
       - .env.example
       - main.py
     - /frontend (Next.js - 나중에 생성)
     - /scripts
     - /docs
     - docker-compose.yml
     - README.md
     - .gitignore

각 디렉토리에 __init__.py 파일을 생성해주세요.
```

### Prompt 1.2: Python 가상환경 및 패키지 설정
```
backend 디렉토리에 Python 가상환경을 설정하고 requirements.txt를 생성해주세요:

필수 패키지:
- fastapi
- uvicorn[standard]
- sqlalchemy
- asyncpg
- psycopg2-binary
- alembic
- pydantic[email]
- pydantic-settings
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- aiofiles
- httpx
- python-dotenv

개발 패키지:
- pytest
- pytest-asyncio
- httpx (테스트용)
- black
- flake8
- mypy

가상환경 생성 및 활성화 스크립트도 만들어주세요.
```

## Phase 2: 데이터베이스 설정

### Prompt 2.1: SQLAlchemy 모델 정의
```
/backend/app/models 디렉토리에 SQLAlchemy 모델을 생성해주세요:

1. base.py - Base 클래스 정의
2. user.py:
   - id (Integer, primary key)
   - email (String, unique, index)
   - hashed_password (String)
   - username (String)
   - is_active (Boolean, default=True)
   - created_at (DateTime)
   - hosting 관계 설정

3. hosting.py:
   - id (Integer, primary key)
   - user_id (Integer, ForeignKey, unique)
   - vm_id (String, unique)
   - vm_ip (String)
   - ssh_port (Integer)
   - status (String) - enum: creating, running, stopping, stopped
   - created_at (DateTime)
   - user 관계 설정

/backend/app/db/base.py에 모든 모델을 import하고,
/backend/app/db/session.py에 데이터베이스 연결 설정을 구현해주세요.
```

### Prompt 2.2: Alembic 마이그레이션 설정
```
Alembic을 사용한 데이터베이스 마이그레이션을 설정해주세요:

1. alembic init 명령으로 초기화
2. alembic.ini 설정 수정 (환경변수에서 DB URL 읽기)
3. env.py 수정:
   - SQLAlchemy 모델 import
   - 비동기 마이그레이션 지원
   
4. 초기 마이그레이션 생성:
   - users 테이블
   - hosting 테이블
   - 인덱스 설정

스크립트에 마이그레이션 실행 명령어도 포함해주세요.
```

## Phase 3: Core 설정 구현

### Prompt 3.1: 설정 관리
```
/backend/app/core 디렉토리에 설정 관리 시스템을 구현해주세요:

1. config.py:
   - Pydantic Settings 사용
   - 환경 변수 관리
   - DATABASE_URL
   - SECRET_KEY (JWT용)
   - ALGORITHM = "HS256"
   - ACCESS_TOKEN_EXPIRE_MINUTES = 1440
   - VM 관련 설정

2. security.py:
   - 비밀번호 해싱 (passlib)
   - JWT 토큰 생성/검증
   - OAuth2PasswordBearer 설정

3. dependencies.py:
   - 데이터베이스 세션 의존성
   - 현재 사용자 가져오기 의존성
```

### Prompt 3.2: Pydantic 스키마 정의
```
/backend/app/schemas 디렉토리에 Pydantic 스키마를 생성해주세요:

1. user.py:
   - UserBase (email, username)
   - UserCreate (+ password)
   - UserInDB (+ hashed_password)
   - User (response 모델)
   - Token, TokenData

2. hosting.py:
   - HostingBase
   - HostingCreate
   - HostingUpdate (status)
   - Hosting (response 모델)
   - HostingDetail (전체 정보)

3. common.py:
   - StandardResponse (success, message, data)
   - ErrorResponse
```

## Phase 4: 인증 시스템 구현

### Prompt 4.1: 인증 엔드포인트
```
/backend/app/api/endpoints/auth.py를 구현해주세요:

1. POST /register:
   - Pydantic 모델로 입력 검증
   - 이메일 중복 확인
   - 비밀번호 해싱
   - 사용자 생성
   - 성공 응답

2. POST /login:
   - OAuth2PasswordRequestForm 사용
   - 이메일/비밀번호 검증
   - JWT 액세스 토큰 생성
   - token_type: "bearer" 포함

3. GET /me:
   - 현재 사용자 정보 반환
   - 인증 필요

FastAPI의 Depends를 활용한 의존성 주입을 사용해주세요.
```

### Prompt 4.2: 사용자 서비스
```
/backend/app/services/user_service.py를 구현해주세요:

비동기 함수로 구현:
1. create_user(db, user_create):
   - 트랜잭션 처리
   - 에러 핸들링

2. get_user_by_email(db, email):
   - 이메일로 사용자 조회

3. authenticate_user(db, email, password):
   - 사용자 인증
   - 비밀번호 검증

4. get_current_user(token, db):
   - JWT 토큰에서 사용자 정보 추출
   - 사용자 존재 확인
```

## Phase 5: VM 관리 서비스 구현

### Prompt 5.1: VM 관리 서비스
```
/backend/app/services/vm_service.py를 구현해주세요:

KVM/QEMU를 사용한 비동기 VM 관리:

1. create_vm(user_id: str) -> dict:
   - virt-install 명령어 사용
   - Ubuntu 20.04 이미지 기반
   - 메모리: 1GB, CPU: 1 core
   - cloud-init으로 초기 설정
   - nginx 자동 설치 스크립트
   - SSH 키 설정
   - 브리지 네트워크 설정
   - VM 정보 반환 (vm_id, ip, ssh_port)

2. delete_vm(vm_id: str) -> bool:
   - virsh destroy 명령
   - virsh undefine 명령
   - 디스크 이미지 삭제

3. get_vm_status(vm_id: str) -> str:
   - virsh domstate 명령
   - 상태 매핑

asyncio.create_subprocess_exec를 사용해주세요.
```

### Prompt 5.2: Nginx 프록시 서비스
```
/backend/app/services/proxy_service.py를 구현해주세요:

1. add_proxy_rule(user_id: str, vm_ip: str, ssh_port: int):
   - Nginx 설정 템플릿 사용
   - /etc/nginx/sites-available/hosting/{user_id}.conf 생성
   - location /{user_id} 블록
   - proxy_pass http://{vm_ip}:80
   - SSH 포트 포워딩 (stream 블록)
   - sites-enabled에 심볼릭 링크
   - nginx -s reload

2. remove_proxy_rule(user_id: str):
   - 설정 파일 삭제
   - 심볼릭 링크 제거
   - nginx -s reload

3. get_random_port() -> int:
   - 10000-20000 범위
   - 사용 중인 포트 확인

템플릿 파일도 /backend/app/templates/nginx.conf.j2로 생성해주세요.
```

## Phase 6: 호스팅 API 구현

### Prompt 6.1: 호스팅 엔드포인트
```
/backend/app/api/endpoints/hosting.py를 구현해주세요:

1. POST /host:
   - 현재 사용자 확인 (Depends)
   - 기존 호스팅 존재 확인
   - VM 생성 (백그라운드 태스크)
   - DB에 상태 'creating' 저장
   - 응답: 호스팅 정보

2. GET /host:
   - 현재 사용자의 호스팅 조회
   - VM 상태 실시간 확인
   - 상세 정보 반환

3. DELETE /host:
   - 호스팅 존재 확인
   - VM 삭제 (백그라운드)
   - 프록시 규칙 제거
   - DB에서 삭제

BackgroundTasks를 사용하여 긴 작업을 비동기로 처리해주세요.
```

### Prompt 6.2: 호스팅 서비스
```
/backend/app/services/hosting_service.py를 구현해주세요:

1. create_hosting(db, user_id):
   - 트랜잭션 처리
   - VM 생성 호출
   - 프록시 설정
   - 상태 업데이트
   - 에러 시 롤백

2. get_user_hosting(db, user_id):
   - 호스팅 정보 조회
   - VM 상태 동기화

3. delete_hosting(db, user_id):
   - 모든 리소스 정리
   - 트랜잭션 보장

4. update_hosting_status(db, hosting_id, status):
   - 상태 업데이트

celery나 background tasks를 고려해주세요.
```

## Phase 7: API 라우터 및 메인 앱

### Prompt 7.1: API 라우터 설정
```
FastAPI 라우터를 설정해주세요:

1. /backend/app/api/api.py:
   - auth 라우터 포함
   - hosting 라우터 포함
   - 프리픽스 설정

2. /backend/main.py:
   - FastAPI 앱 생성
   - CORS 미들웨어 설정 (Next.js용)
   - 라우터 포함
   - 전역 예외 처리
   - health check 엔드포인트
   - Swagger UI 설정

3. /backend/app/core/exceptions.py:
   - 커스텀 예외 클래스
   - 예외 핸들러
```

### Prompt 7.2: 유틸리티 구현
```
/backend/app/utils 디렉토리에 유틸리티 함수들을 구현해주세요:

1. vm_utils.py:
   - cloud-init 설정 생성
   - VM 이름 생성 규칙
   - IP 주소 할당 관리

2. ssh_utils.py:
   - SSH 키 쌍 생성
   - authorized_keys 설정

3. logger.py:
   - 구조화된 로깅 설정
   - 파일 및 콘솔 출력

4. validators.py:
   - 이메일 검증
   - 포트 범위 검증
```

## Phase 8: 테스트 구현

### Prompt 8.1: 테스트 설정
```
/backend/tests 디렉토리에 pytest 테스트를 설정해주세요:

1. conftest.py:
   - 테스트 DB 설정
   - 테스트 클라이언트
   - 테스트 사용자 fixture
   - 인증 토큰 fixture

2. test_auth.py:
   - 회원가입 테스트
   - 로그인 테스트
   - 토큰 검증 테스트
   - 중복 이메일 테스트

3. test_hosting.py:
   - 호스팅 생성 테스트
   - 호스팅 조회 테스트
   - 호스팅 삭제 테스트
   - 권한 테스트

pytest-asyncio를 사용하여 비동기 테스트를 작성해주세요.
```

## Phase 9: Docker 및 배포 설정

### Prompt 9.1: Docker 구성
```
Docker 파일들을 생성해주세요:

1. /backend/Dockerfile:
   - Python 3.10 slim 이미지
   - 시스템 패키지 설치 (libvirt, qemu)
   - Python 패키지 설치
   - 앱 복사 및 실행

2. docker-compose.yml:
   - backend 서비스
   - postgres 서비스
   - nginx 서비스
   - 볼륨 설정 (VM 이미지, nginx 설정)
   - 네트워크 설정

3. docker-compose.dev.yml:
   - 개발용 오버라이드
   - 볼륨 마운트
   - 환경 변수

4. .env.example:
   DATABASE_URL=postgresql://user:pass@localhost/dbname
   SECRET_KEY=your-secret-key
   VM_BRIDGE_NAME=virbr0
   VM_IMAGE_PATH=/var/lib/libvirt/images
```

### Prompt 9.2: 배포 스크립트
```
/scripts 디렉토리에 배포 스크립트를 작성해주세요:

1. setup-host.sh:
   - Ubuntu 22.04 시스템 패키지 설치
   - KVM/QEMU 설치 및 설정
   - libvirt 네트워크 설정
   - Python 3.10 설치
   - PostgreSQL 14 설치
   - Nginx 설치

2. init-vm-template.sh:
   - Ubuntu 20.04 cloud 이미지 다운로드
   - 기본 VM 템플릿 생성
   - cloud-init 설정

3. deploy.sh:
   - Git pull
   - 가상환경 활성화
   - pip 패키지 업데이트
   - Alembic 마이그레이션
   - systemd 서비스 재시작
```

## Phase 10: 문서화 및 모니터링

### Prompt 10.1: API 문서화
```
FastAPI의 자동 문서화를 개선하고 추가 문서를 작성해주세요:

1. 각 엔드포인트에 상세한 docstring 추가:
   - 설명
   - 파라미터 설명
   - 응답 예시
   - 에러 코드

2. /docs/API.md:
   - 전체 API 개요
   - 인증 플로우
   - 사용 예시 (curl, httpie)
   - 에러 코드 표

3. Pydantic 모델에 example 추가:
   - Config 클래스에 schema_extra
```

### Prompt 10.2: 구현 보고서
```
/docs/implementation-report.md를 작성해주세요:

다음 다이어그램을 Mermaid로 작성:

1. 시스템 아키텍처:
   - 컴포넌트 관계
   - 데이터 플로우

2. VM 생성 시퀀스:
   - API 호출부터 VM 생성까지

3. 데이터베이스 ERD

4. 보안 아키텍처:
   - JWT 인증 플로우
   - VM 격리

5. 배포 아키텍처:
   - Docker 컨테이너 구성
   - 네트워크 토폴로지

각 섹션에 스크린샷과 설명을 포함해주세요.
```

## 추가 고려사항

- FastAPI의 async/await를 최대한 활용
- Pydantic의 타입 검증 활용
- 에러 처리와 로깅 철저히
- 보안 (SQL Injection, XSS 방지)
- 성능 최적화 (연결 풀링, 캐싱)

---

# 🚀 현재 상황별 추가 Phase (2025-06-14 기준)

## 현재 상태: 약 80% 구현 완료
- ✅ 백엔드 API 및 VM 관리 완료
- ✅ 프론트엔드 UI 완료
- ❌ **Nginx 프록시 서비스 미구현** (핵심)
- ❌ VM 내부 웹서버 설정 미구현

---

## Phase 11: 핵심 미구현 기능 완성 (최우선)

### Prompt 11.1: Nginx 프록시 서비스 구현
```
현재 프로젝트의 핵심 미구현 부분인 Nginx 프록시 서비스를 구현해주세요:

/backend/app/services/proxy_service.py를 생성:

1. ProxyService 클래스:
   - Nginx 설정 파일 경로 관리
   - 템플릿 엔진 (Jinja2) 사용

2. add_proxy_rule(user_id: str, vm_ip: str, ssh_port: int):
   - 웹 포트 포워딩: /<user_id> → http://vm_ip:80
   - SSH 포트 포워딩: :{ssh_port} → vm_ip:22
   - Nginx 설정 파일 생성 (/etc/nginx/sites-available/hosting/{user_id}.conf)
   - sites-enabled에 심볼릭 링크 생성
   - nginx -t로 설정 검증
   - nginx -s reload로 리로드

3. remove_proxy_rule(user_id: str):
   - 설정 파일 삭제
   - 심볼릭 링크 제거
   - nginx -s reload

4. get_random_port(start=10000, end=20000):
   - 사용 가능한 포트 검색
   - 포트 충돌 방지

현재 backend/app/core/config.py에 NGINX_CONFIG_PATH 설정이 있으니 활용해주세요.
```

### Prompt 11.2: Nginx 설정 템플릿 생성
```
/backend/templates/nginx.conf.j2 파일을 생성해주세요:

Jinja2 템플릿 내용:
1. 웹 서비스 location 블록:
   - location /{{ user_id }} { ... }
   - proxy_pass http://{{ vm_ip }}:80;
   - proxy_set_header 설정들
   - 에러 처리

2. 추가로 /backend/templates/ 디렉토리에:
   - nginx-site.conf.j2 (개별 호스팅용)
   - nginx-main.conf.j2 (메인 설정용)

3. 템플릿 변수:
   - user_id: 사용자 ID
   - vm_ip: VM IP 주소
   - ssh_port: SSH 포트 번호
   - domain: 서비스 도메인
```

### Prompt 11.3: VM 웹서버 자동 설치 구현
```
/backend/app/services/vm_service.py를 수정하여 VM에 웹서버를 자동 설치하도록 해주세요:

1. create_cloud_init_config(vm_id: str) 메서드 추가:
   - cloud-init user-data 생성
   - Nginx 자동 설치 스크립트
   - 기본 웹 페이지 생성 (/var/www/html/index.html)
   - SSH 사용자 설정 (ubuntu 사용자)
   - authorized_keys 설정

2. create_vm() 메서드 수정:
   - cloud-init ISO 이미지 생성
   - VM 생성 시 cloud-init 연결
   - 웹서버 설치 완료 대기

3. 기본 웹 페이지 템플릿:
   - 사용자별 환영 페이지
   - 호스팅 정보 표시
   - 파일 업로드 안내

현재 VM 생성 로직이 있으니 확장하는 형태로 구현해주세요.
```

### Prompt 11.4: 호스팅 서비스와 프록시 연동
```
/backend/app/services/hosting_service.py를 수정하여 프록시 서비스와 연동해주세요:

1. create_hosting() 메서드 수정:
   - VM 생성 완료 후 프록시 규칙 자동 추가
   - 프록시 설정 실패 시 VM 삭제 (롤백)
   - 전체 과정을 트랜잭션으로 처리

2. delete_hosting() 메서드 수정:
   - VM 삭제 전 프록시 규칙 제거
   - 순서: 프록시 제거 → VM 삭제 → DB 삭제

3. 에러 처리 강화:
   - ProxyService import 추가
   - 각 단계별 실패 시 롤백 로직
   - 상세한 에러 메시지

현재 hosting_service.py가 12KB로 구현되어 있으니 기존 로직을 수정하는 형태로 해주세요.
```

## Phase 12: Docker 환경 완성

### Prompt 12.1: Nginx 컨테이너 활성화
```
docker-compose.yml의 Nginx 서비스를 활성화하고 완성해주세요:

현재 Nginx 서비스가 정의되어 있지만 완전하지 않습니다:

1. nginx 서비스 완성:
   - 포트 80, 443 매핑
   - 볼륨 마운트 (설정 파일, 로그)
   - backend 서비스와 네트워크 연결
   - depends_on 설정

2. /nginx 디렉토리 생성:
   - nginx/nginx.conf (메인 설정)
   - nginx/sites/ (호스팅별 설정 저장)
   - nginx/ssl/ (SSL 인증서용)

3. 네트워크 설정:
   - 내부 통신용 네트워크
   - VM 접근용 브리지 설정

현재 docker-compose.yml에 nginx 서비스가 있으니 수정해주세요.
```

### Prompt 12.2: 프로덕션 환경 설정
```
프로덕션 배포를 위한 환경 설정을 완성해주세요:

1. docker-compose.prod.yml 생성:
   - 프로덕션 전용 설정
   - 환경변수 외부화
   - 로그 설정
   - 리소스 제한

2. .env.production.example 업데이트:
   - SECURITY.md 내용 반영
   - 모든 필요한 환경변수 포함
   - 보안 주의사항 주석

3. nginx/nginx.conf 프로덕션 설정:
   - SSL/TLS 설정
   - 보안 헤더
   - Rate limiting
   - 로그 설정

SECURITY.md 파일의 보안 가이드를 참고해주세요.
```

## Phase 13: 통합 테스트 및 검증

### Prompt 13.1: 전체 플로우 테스트
```
전체 호스팅 생성 플로우를 테스트하는 코드를 작성해주세요:

/backend/tests/test_full_flow.py:

1. test_complete_hosting_flow():
   - 사용자 회원가입
   - 로그인 및 토큰 발급
   - 호스팅 생성 요청
   - VM 생성 대기
   - 프록시 설정 확인
   - 웹 접속 테스트 (http://localhost/{user_id})
   - SSH 접속 테스트
   - 호스팅 삭제
   - 리소스 정리 확인

2. test_error_scenarios():
   - VM 생성 실패 시나리오
   - 프록시 설정 실패 시나리오
   - 네트워크 오류 시나리오
   - 롤백 동작 검증

3. test_concurrent_hosting():
   - 동시 호스팅 생성 테스트
   - 포트 충돌 방지 테스트
   - 리소스 경합 처리

현재 backend/tests/ 디렉토리가 있으니 활용해주세요.
```

### Prompt 13.2: API 엔드포인트 최종 검증
```
모든 API 엔드포인트가 정상 동작하는지 검증해주세요:

1. 인증 API 테스트:
   - POST /api/v1/auth/register
   - POST /api/v1/auth/login
   - POST /api/v1/auth/token
   - GET /api/v1/auth/me

2. 호스팅 API 테스트:
   - POST /api/v1/host (호스팅 생성)
   - GET /api/v1/host/my (내 호스팅 조회)
   - DELETE /api/v1/host/my (호스팅 삭제)

3. 각 엔드포인트별 검증 스크립트:
   - curl 명령어 예시
   - 응답 데이터 검증
   - 에러 케이스 처리

4. 실제 브라우저에서 접속 테스트:
   - http://localhost/{user_id} 접속
   - ssh -p {port} ubuntu@localhost 접속

검증 결과를 README.md에 스크린샷과 함께 문서화해주세요.
```

## Phase 14: 문서화 및 배포 준비

### Prompt 14.1: 구현 보고서 작성
```
/docs/implementation-report.md를 작성해주세요:

TODO.md를 참고하여 다음 내용 포함:

1. 시스템 아키텍처 다이어그램 (Mermaid):
   - 전체 구성 요소 관계
   - 데이터 플로우
   - 네트워크 구성

2. 구현 상세 내용:
   - 각 컴포넌트별 구현 내용
   - 주요 기술 스택 설명
   - 핵심 알고리즘 설명

3. 배포 및 설치 가이드:
   - Clean Ubuntu 22.04 기준
   - Docker 설치 및 실행
   - 환경 설정 방법

4. API 사용 예시:
   - curl 명령어 예시
   - 각 단계별 스크린샷
   - 트러블슈팅 가이드

5. 성능 및 제한사항:
   - 동시 사용자 수
   - 리소스 사용량
   - 알려진 이슈

현재 PRD.md와 TODO.md 내용을 종합해주세요.
```

### Prompt 14.2: README.md 최종 업데이트
```
README.md를 최종 사용자 관점에서 업데이트해주세요:

1. 프로젝트 소개:
   - 완성된 기능 목록
   - 실제 사용 시연 스크린샷
   - 기술 스택 명시

2. 빠른 시작 가이드:
   - git clone부터 서비스 실행까지
   - Docker 기반 원클릭 실행
   - 첫 호스팅 생성 예시

3. 주요 기능 설명:
   - 웹 호스팅 자동 생성
   - SSH/SFTP 접속
   - 프록시를 통한 웹 접속
   - 관리 대시보드

4. 개발자 가이드:
   - 로컬 개발 환경 설정
   - 테스트 실행 방법
   - 기여 방법

5. 라이선스 및 연락처 정보

완성된 프로젝트임을 강조하는 내용으로 작성해주세요.
```

## Phase 15: 최종 검토 및 완성

### Prompt 15.1: 보안 검토 및 강화
```
SECURITY.md를 참고하여 보안 설정을 최종 검토해주세요:

1. 시크릿 키 및 인증서:
   - 개발용 키 → 프로덕션 키 변경 확인
   - JWT 시크릿 키 강도 검증
   - 데이터베이스 비밀번호 검증

2. 네트워크 보안:
   - VM 간 격리 설정
   - 방화벽 규칙 설정
   - 불필요한 포트 차단

3. 권한 관리:
   - 최소 권한 원칙 적용
   - sudo 권한 최소화
   - 파일 권한 설정

4. 보안 테스트:
   - SQL Injection 테스트
   - XSS 방지 확인
   - 인증 우회 시도

보안 이슈 발견 시 즉시 수정하고 문서화해주세요.
```

### Prompt 15.2: 성능 최적화 및 최종 테스트
```
프로덕션 준비를 위한 최종 성능 최적화를 수행해주세요:

1. 성능 벤치마크:
   - API 응답 시간 측정
   - VM 생성 시간 측정
   - 동시 사용자 처리 능력
   - 메모리 및 CPU 사용량

2. 최적화 작업:
   - 데이터베이스 쿼리 최적화
   - 캐싱 전략 적용
   - 연결 풀 설정
   - 비동기 처리 개선

3. 부하 테스트:
   - 동시 호스팅 생성 테스트
   - 대용량 파일 전송 테스트
   - 장시간 운영 안정성 테스트

4. 모니터링 설정:
   - 로그 레벨 조정
   - 메트릭 수집 설정
   - 알림 시스템 구축

성능 테스트 결과를 문서화하고 개선사항을 적용해주세요.
```

---

## 🎯 완성 체크리스트

### Phase 11 완료 후 달성 목표:
- [ ] 웹 서비스 접속 가능: `http://localhost/{user_id}`
- [ ] SSH 접속 가능: `ssh -p {port} ubuntu@localhost`
- [ ] 프록시 서비스 완전 동작
- [ ] VM 내부 웹서버 자동 설치

### Phase 12-13 완료 후 달성 목표:
- [ ] Docker 환경에서 완전 동작
- [ ] 모든 API 엔드포인트 검증 완료
- [ ] 통합 테스트 통과

### Phase 14-15 완료 후 달성 목표:
- [ ] 문서화 완료
- [ ] 보안 검토 완료
- [ ] 성능 최적화 완료
- [ ] 프로덕션 배포 준비 완료

---

**다음 단계**: Phase 11.1 Nginx 프록시 서비스 구현부터 시작하세요.