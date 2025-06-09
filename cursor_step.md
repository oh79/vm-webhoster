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