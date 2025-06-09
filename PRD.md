# 웹 호스팅 서비스 PRD (Product Requirements Document)

## 1. 프로젝트 개요

### 1.1 목적
사용자가 간단하게 웹 호스팅을 신청하고 관리할 수 있는 자동화된 웹 호스팅 서비스 구축

### 1.2 주요 기능
- 사용자 인증 시스템 (회원가입/로그인)
- 자동 VM 생성 및 웹서버 설정
- Reverse Proxy를 통한 웹 서비스 접근
- SSH/SFTP 접근 지원
- 호스팅 상태 관리

## 2. 시스템 아키텍처

### 2.1 구성 요소
1. **프론트엔드**: 사용자 인터페이스
2. **백엔드 서버**: API 서버 및 비즈니스 로직
3. **웹서버/프록시 서버**: Nginx/Apache Reverse Proxy
4. **가상머신 관리**: VM 생성/삭제 자동화
5. **데이터베이스**: 사용자 및 호스팅 정보 저장

### 2.2 기술 스택
- **Backend**: Python/FastAPI
- **Frontend**: Next.js 14 (App Router)
- **Database**: PostgreSQL
- **Reverse Proxy**: Nginx
- **VM Management**: KVM/QEMU
- **Authentication**: JWT
- **ORM**: SQLAlchemy
- **Validation**: Pydantic

## 3. 기능 요구사항

### 3.1 사용자 인증
- **회원가입 (POST /register)**
  - 이메일, 비밀번호, 사용자명 입력
  - 이메일 중복 검사
  - 비밀번호 해싱 (bcrypt)

- **로그인 (POST /login)**
  - 이메일, 비밀번호 인증
  - JWT 토큰 발급
  - 토큰 만료 시간 설정

### 3.2 호스팅 관리
- **호스팅 신청 (POST /host)**
  - 인증된 사용자만 접근 가능
  - 사용자당 1개 호스팅 제한
  - VM 자동 생성
  - 웹서버 자동 설치 및 설정
  - 고유 ID 할당

- **호스팅 조회 (GET /host)**
  - 현재 호스팅 상태 확인
  - VM 정보 (IP, 포트, 상태)
  - 접속 URL 정보

- **호스팅 삭제 (DELETE /host)**
  - VM 자동 삭제
  - 관련 프록시 설정 제거
  - DB 정보 정리

### 3.3 프록시 설정
- **웹 서비스 접근**
  - URL 패턴: `<service-domain>/<user-id>` → VM의 80번 포트
  - Nginx location 블록 자동 생성

- **SSH/SFTP 접근**
  - 랜덤 포트 할당: `<service-domain>:<random-port>` → VM의 22번 포트
  - 포트 포워딩 설정

## 4. 데이터베이스 스키마

### 4.1 Users 테이블
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 Hosting 테이블
```sql
CREATE TABLE hosting (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    vm_id VARCHAR(100) UNIQUE NOT NULL,
    vm_ip VARCHAR(15) NOT NULL,
    ssh_port INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 5. API 명세

### 5.1 회원가입
```
POST /register
Content-Type: application/json

Request:
{
    "email": "user@example.com",
    "password": "password123",
    "username": "username"
}

Response:
{
    "success": true,
    "message": "User registered successfully"
}
```

### 5.2 로그인
```
POST /login
Content-Type: application/json

Request:
{
    "email": "user@example.com",
    "password": "password123"
}

Response:
{
    "success": true,
    "token": "jwt-token-here"
}
```

### 5.3 호스팅 신청
```
POST /host
Authorization: Bearer <token>

Response:
{
    "success": true,
    "data": {
        "vm_id": "user123",
        "web_url": "https://service.com/user123",
        "ssh_port": 12345,
        "ssh_command": "ssh -p 12345 user@service.com"
    }
}
```

### 5.4 호스팅 조회
```
GET /host
Authorization: Bearer <token>

Response:
{
    "success": true,
    "data": {
        "vm_id": "user123",
        "status": "running",
        "web_url": "https://service.com/user123",
        "ssh_port": 12345,
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

### 5.5 호스팅 삭제
```
DELETE /host
Authorization: Bearer <token>

Response:
{
    "success": true,
    "message": "Hosting deleted successfully"
}
```

## 6. 보안 고려사항

- JWT 토큰 검증
- SQL Injection 방지
- XSS 방지
- CORS 설정
- VM 격리
- SSH 키 기반 인증
- Rate Limiting

## 7. 성능 요구사항

- VM 생성 시간: 5분 이내
- API 응답 시간: 500ms 이내
- 동시 사용자: 100명 이상
- 시스템 가용성: 99.9%

## 8. 개발 환경

- Ubuntu 22.04 LTS
- Python 3.10+
- Node.js 18+ (Next.js용)
- PostgreSQL 14+
- Nginx 1.18+
- Git/GitHub
- Cursor IDE
- v0 (프론트엔드 개발)

## 9. 배포 요구사항

- Docker 컨테이너화
- 환경 변수 관리
- 로깅 시스템
- 모니터링 설정
- 백업 전략

## 10. 테스트 요구사항

- 단위 테스트
- 통합 테스트
- API 테스트
- 부하 테스트
- 보안 테스트