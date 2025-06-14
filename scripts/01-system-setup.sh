#!/bin/bash

# 🚀 1단계: 시스템 초기 설정
# 시스템 업데이트 및 필수 패키지 설치

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

echo -e "${GREEN}🚀 1단계: 시스템 초기 설정 시작${NC}"
echo "================================================"

# 시스템 정보 확인
log_step "시스템 정보 확인"
echo "  - OS: $(lsb_release -d | cut -f2)"
echo "  - Kernel: $(uname -r)"
echo "  - Architecture: $(uname -m)"
echo "  - Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  - Disk: $(df -h / | awk 'NR==2 {print $4}') available"

# 시스템 업데이트
log_step "시스템 패키지 업데이트"
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
log_step "필수 패키지 설치"
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    pkg-config \
    libpq-dev \
    net-tools \
    htop \
    vim \
    tree

log_success "필수 패키지 설치 완료"

# Docker 설치
log_step "Docker 설치"
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

log_success "Docker 설치 완료"

# Node.js 설치
log_step "Node.js 18.x 설치"
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

echo "  - Node.js: $(node --version)"
echo "  - npm: $(npm --version)"

log_success "Node.js 설치 완료"

# PostgreSQL 설치
log_step "PostgreSQL 설치"
sudo apt install -y postgresql postgresql-contrib

sudo systemctl start postgresql
sudo systemctl enable postgresql

log_success "PostgreSQL 설치 완료"

# Redis 설치
log_step "Redis 설치"
sudo apt install -y redis-server

sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sudo systemctl restart redis-server
sudo systemctl enable redis-server

log_success "Redis 설치 완료"

# 방화벽 설정
log_step "기본 방화벽 설정"
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

log_success "방화벽 설정 완료"

echo -e "${GREEN}✅ 1단계: 시스템 초기 설정 완료${NC}"
echo "================================================"
echo "다음 단계: ./scripts/02-project-setup.sh" 