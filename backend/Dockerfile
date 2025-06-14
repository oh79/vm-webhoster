# Python 3.10 slim 베이스 이미지 사용
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    # 기본 도구
    curl \
    wget \
    git \
    unzip \
    # 컴파일러 및 개발 도구
    gcc \
    g++ \
    make \
    pkg-config \
    # Python 개발 도구
    python3-dev \
    # 네트워킹 도구 (간소화)
    net-tools \
    iputils-ping \
    # VM 관리 도구 (최소한)
    qemu-utils \
    # 정리
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 사용자 계정 생성 (보안 강화)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Python 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# VM 이미지 및 설정 디렉토리 생성
RUN mkdir -p /app/vm-images \
    && mkdir -p /app/nginx-configs \
    && mkdir -p /app/cloud-init \
    && mkdir -p /var/log/webhoster

# 권한 설정
RUN chown -R appuser:appuser /app \
    && chmod +x /app/main.py

# 설정 파일들을 위한 볼륨 마운트 포인트 생성
VOLUME ["/app/vm-images", "/app/nginx-configs", "/var/log/webhoster"]

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 애플리케이션 실행 (non-root 사용자로)
USER appuser

# 시작 스크립트 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 