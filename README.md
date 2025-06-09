# 웹 호스팅 서비스

자동화된 VM 기반 웹 호스팅 서비스 구현 프로젝트

## 📋 프로젝트 개요

사용자가 간단하게 웹 호스팅을 신청하고 관리할 수 있는 자동화된 웹 호스팅 서비스입니다.

### 주요 기능
- 🔐 사용자 인증 시스템 (회원가입/로그인)
- 🖥️ 자동 VM 생성 및 웹서버 설정
- 🔄 Reverse Proxy를 통한 웹 서비스 접근
- 🔑 SSH/SFTP 접근 지원
- 📊 호스팅 상태 관리

## 🛠️ 기술 스택

- **Backend**: Python 3.10+ / FastAPI
- **Frontend**: Next.js 14 (App Router)
- **Database**: PostgreSQL 14+
- **Reverse Proxy**: Nginx
- **VM Management**: KVM/QEMU
- **Authentication**: JWT
- **ORM**: SQLAlchemy
- **Validation**: Pydantic

## 📁 프로젝트 구조

```
vm-webhoster/
├── backend/                 # Python/FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 엔드포인트
│   │   ├── core/           # 핵심 설정 (config, security)
│   │   ├── db/             # 데이터베이스 설정
│   │   ├── models/         # SQLAlchemy 모델
│   │   ├── schemas/        # Pydantic 스키마
│   │   ├── services/       # 비즈니스 로직
│   │   └── utils/          # 유틸리티 함수
│   ├── tests/              # 테스트 코드
│   ├── alembic/            # DB 마이그레이션
│   ├── templates/          # 설정 템플릿
│   └── main.py             # FastAPI 애플리케이션
├── frontend/               # Next.js 프론트엔드 (예정)
├── scripts/                # 배포 및 설정 스크립트
├── docs/                   # 프로젝트 문서
└── docker-compose.yml      # Docker 구성
```

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone <repository-url>
cd vm-webhoster
```

### 2. Python 가상환경 설정
```bash
./scripts/setup_venv.sh
```

### 3. 환경 변수 설정
```bash
cd backend
cp config.env.example .env
# .env 파일을 편집하여 실제 설정값 입력
```

### 4. 데이터베이스 설정 (개발용)
```bash
# PostgreSQL 설치 및 설정
sudo apt install postgresql postgresql-contrib
sudo -u postgres createuser --interactive
sudo -u postgres createdb webhoster_db
```

### 5. 애플리케이션 실행
```bash
cd backend
source venv/bin/activate
python main.py
```

## 🐳 Docker로 실행

```bash
# 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 📚 API 문서

애플리케이션 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 추가적인 엔드포인트 설명은 [docs/API.md](docs/API.md) 파일을 참고하세요.

## 🔧 개발 환경

- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.10+
- **Node.js**: 18+ (프론트엔드용)
- **IDE**: Cursor IDE

## 📖 개발 단계

현재 **Phase 1 (프로젝트 초기 설정)** 완료:
- ✅ 프로젝트 구조 생성
- ✅ Python 가상환경 설정
- ✅ Docker 설정
- ✅ 기본 FastAPI 애플리케이션

### 다음 단계
- Phase 2: 데이터베이스 설정 (SQLAlchemy 모델, Alembic)
- Phase 3: Core 설정 구현 (Config, Security, Dependencies)
- Phase 4: 인증 시스템 구현
- Phase 5: VM 관리 서비스 구현

## 🤝 기여

PRD.md 파일을 참조하여 요구사항을 확인하고 기여해주세요.

## 📄 라이선스

MIT License
