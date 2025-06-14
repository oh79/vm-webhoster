"""
VM 웹호스터 애플리케이션 패키지
"""
from app.core.config import settings

__version__ = settings.VERSION
__description__ = settings.DESCRIPTION

# 패키지 정보
__author__ = "VM WebHoster Team"
__license__ = "MIT"

# 주요 컴포넌트 export
from app.main import app

__all__ = [
    "app",
    "__version__",
    "__description__"
]
