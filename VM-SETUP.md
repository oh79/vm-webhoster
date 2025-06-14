# VM 환경 설정 가이드

SSH로 원격 Ubuntu 22.04 VM에 접속하여 개발하고, 로컬 환경에서 프론트엔드에 접속하는 환경 설정 가이드입니다.

## 📋 개요

- **개발 환경**: SSH로 접속한 원격 Ubuntu 22.04 VM
- **테스트/평가 환경**: 로컬 환경(Windows/Mac)에서 프론트엔드 접속
- **아키텍처**: Docker Compose 기반 마이크로서비스

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 1. VM IP 주소 확인
./scripts/get-vm-ip.sh

# 2. 환경 변수 파일 생성
cp backend/config.env.example .env

# 3. IP 주소 설정 (YOUR_VM_IP를 실제 IP로 변경)
sed -i 's/YOUR_VM_IP/실제_VM_IP/g' .env
```

### 2. 서비스 시작

```bash
# Docker Compose로 모든 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

### 3. 접속 확인

- **프론트엔드**: `http://VM_IP:3000`
- **백엔드 API**: `http://VM_IP:8000`
- **API 문서**: `http://VM_IP:8000/docs`

## 🔧 상세 설정

### 환경 변수 설정

`.env` 파일에서 다음 항목들을 실제 환경에 맞게 수정하세요:

```bash
# VM의 외부 IP 주소 (필수!)
SERVICE_DOMAIN=192.168.1.100:80
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000
CORS_ORIGINS=["http://192.168.1.100:3000", "http://localhost:3000"]

# 보안 설정 (프로덕션에서는 반드시 변경!)
SECRET_KEY=super-secret-jwt-key-change-in-production-12345
POSTGRES_PASSWORD=webhoster_pass

# 외부 접근 허용
BIND_ADDRESS=0.0.0.0
API_HOST=0.0.0.0
```

### 방화벽 설정

```bash
# 필요한 포트 열기
sudo ufw allow 3000  # Next.js 프론트엔드
sudo ufw allow 8000  # FastAPI 백엔드
sudo ufw allow 80    # Nginx HTTP
sudo ufw allow 443   # Nginx HTTPS (필요시)

# 방화벽 상태 확인
sudo ufw status
```

## 📂 서비스 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Frontend | 3000 | Next.js 개발 서버 |
| Backend | 8000 | FastAPI 서버 |
| Nginx | 80, 443 | 리버스 프록시 |
| PostgreSQL | 5432 | 데이터베이스 |
| Redis | 6379 | 캐싱 서버 |

## 🛠 개발 워크플로우

### 1. SSH로 VM 접속
```bash
ssh user@vm-ip-address
cd /path/to/vm-webhoster
```

### 2. 코드 수정 및 테스트
```bash
# 백엔드 로그 확인
docker-compose logs -f backend

# 프론트엔드 로그 확인
docker-compose logs -f frontend

# 전체 서비스 재시작
docker-compose restart
```

### 3. 로컬에서 접속 테스트
- 브라우저에서 `http://VM_IP:3000` 접속
- API 테스트: `http://VM_IP:8000/docs`

## 🔍 트러블슈팅

### IP 주소 확인이 안 될 때
```bash
# 다양한 방법으로 IP 확인
curl ifconfig.me
ip addr show
hostname -I
```

### 포트 접속이 안 될 때
```bash
# 포트 상태 확인
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Docker 서비스 상태 확인
docker-compose ps
docker-compose logs service-name
```

### 방화벽 문제
```bash
# 방화벽 비활성화 (테스트용)
sudo ufw disable

# 특정 포트만 허용
sudo ufw allow from any to any port 3000
sudo ufw allow from any to any port 8000
```

## 🔒 보안 고려사항

### 개발/테스트 환경
- 방화벽을 열어두지만, 실제 운영시에는 보안 그룹 설정 필요
- 기본 비밀번호들을 실제 운영에서는 반드시 변경

### 운영 환경 준비사항
1. SSL 인증서 설정 (Let's Encrypt)
2. 도메인 연결 및 DNS 설정
3. 보안 강화 (비밀번호, 방화벽 규칙)
4. 모니터링 및 로깅 설정

## 📞 도움이 필요할 때

### 로그 확인
```bash
# 전체 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs frontend

# 실시간 로그 모니터링
docker-compose logs -f --tail=100
```

### 서비스 재시작
```bash
# 특정 서비스만 재시작
docker-compose restart backend
docker-compose restart frontend

# 전체 재시작
docker-compose down && docker-compose up -d
```

---

**참고**: 이 설정은 개발/테스트 환경을 위한 것입니다. 실제 운영 환경에서는 추가적인 보안 설정이 필요합니다. 