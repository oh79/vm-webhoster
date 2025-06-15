"""
애플리케이션 설정 관리
"""
import os
from functools import lru_cache
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 프로젝트 경로 설정
    PROJECT_ROOT: str = Field(
        default_factory=lambda: str(Path(__file__).parent.parent.parent.parent),
        description="프로젝트 루트 디렉토리 경로"
    )
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", description="서버 호스트")
    PORT: int = Field(default=8000, description="서버 포트")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="허용된 호스트 목록")
    
    # 데이터베이스 설정 (개발용 SQLite)
    DATABASE_URL: str = Field(
        default="sqlite:///./webhoster_dev.db",
        description="데이터베이스 연결 URL"
    )
    
    # JWT 설정
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-this-in-production",
        description="JWT 토큰 서명용 비밀 키"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT 알고리즘")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="액세스 토큰 만료 시간 (분)")
    
    # Rate Limiting 설정
    RATE_LIMIT_CALLS: int = Field(default=100, description="Rate limit 요청 수")
    RATE_LIMIT_PERIOD: int = Field(default=60, description="Rate limit 시간 주기 (초)")
    
    # VM 관리 설정
    VM_BRIDGE_NAME: str = Field(default="virbr0", description="VM 브리지 네트워크 이름")
    VM_IMAGE_PATH: str = Field(default="/var/lib/libvirt/images", description="VM 이미지 저장 경로")
    VM_TEMPLATE_IMAGE: str = Field(default="ubuntu-22.04-server-cloudimg-amd64.img", description="VM 템플릿 이미지")
    VM_DEFAULT_MEMORY: int = Field(default=1024, description="VM 기본 메모리 (MB)")
    VM_DEFAULT_VCPUS: int = Field(default=1, description="VM 기본 vCPU 수")
    VM_DEFAULT_DISK_SIZE: int = Field(default=20, description="VM 기본 디스크 크기 (GB)")
    
    # 보안 설정
    SSH_KEY_SIZE: int = Field(default=2048, description="SSH 키 크기 (bits)")
    SSH_KEY_TYPE: str = Field(default="rsa", description="SSH 키 타입")
    ENABLE_SSH_PASSWORD_AUTH: bool = Field(default=False, description="SSH 패스워드 인증 허용")
    
    # 헬스체크 설정
    HEALTH_CHECK_INTERVAL: int = Field(default=300, description="헬스체크 간격 (초)")
    HEALTH_CHECK_TIMEOUT: int = Field(default=30, description="헬스체크 타임아웃 (초)")
    ENABLE_AUTO_RECOVERY: bool = Field(default=True, description="자동 복구 활성화")
    
    # 네트워크 설정
    NETWORK_TIMEOUT: int = Field(default=30, description="네트워크 연결 타임아웃 (초)")
    MAX_CONCURRENT_VMS: int = Field(default=10, description="최대 동시 VM 수")
    
    # 백업 설정
    ENABLE_CONFIG_BACKUP: bool = Field(default=True, description="설정 백업 활성화")
    BACKUP_RETENTION_DAYS: int = Field(default=7, description="백업 보관 일수")
    
    # 로깅 설정 확장
    ENABLE_VM_LOGGING: bool = Field(default=True, description="VM 생성/삭제 로깅 활성화")
    ENABLE_SECURITY_LOGGING: bool = Field(default=True, description="보안 이벤트 로깅 활성화")
    
    # 서비스 도메인 설정
    SERVICE_DOMAIN: str = Field(default="localhost:8000", description="서비스 도메인")
    NGINX_CONFIG_PATH: str = Field(default="/etc/nginx/sites-available/hosting", description="Nginx 설정 파일 경로")
    
    # SSH 포트 범위 설정
    SSH_PORT_RANGE_START: int = Field(default=10000, description="SSH 포트 범위 시작")
    SSH_PORT_RANGE_END: int = Field(default=10200, description="SSH 포트 범위 끝")
    
    # 개발 환경 설정
    DEBUG: bool = Field(default=True, description="디버그 모드")
    LOG_LEVEL: str = Field(default="INFO", description="로그 레벨")
    LOG_FILE: Optional[str] = Field(default=None, description="로그 파일 경로")
    
    # 프로젝트 정보
    PROJECT_NAME: str = Field(default="웹 호스팅 서비스", description="프로젝트 이름")
    VERSION: str = Field(default="1.0.0", description="프로젝트 버전")
    DESCRIPTION: str = Field(default="자동화된 VM 기반 웹 호스팅 서비스", description="프로젝트 설명")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 추가 필드 허용

@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐싱됨)"""
    return Settings()

# 전역 설정 인스턴스
settings = get_settings() 