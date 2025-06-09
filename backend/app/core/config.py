"""
애플리케이션 설정 관리
"""
import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
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
    VM_TEMPLATE_IMAGE: str = Field(default="ubuntu-20.04-server-cloudimg-amd64.img", description="VM 템플릿 이미지")
    
    # 서비스 도메인 설정
    SERVICE_DOMAIN: str = Field(default="localhost:8000", description="서비스 도메인")
    NGINX_CONFIG_PATH: str = Field(default="/etc/nginx/sites-available/hosting", description="Nginx 설정 파일 경로")
    
    # SSH 포트 범위 설정
    SSH_PORT_RANGE_START: int = Field(default=10000, description="SSH 포트 범위 시작")
    SSH_PORT_RANGE_END: int = Field(default=20000, description="SSH 포트 범위 끝")
    
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