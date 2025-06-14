"""
로깅 관련 유틸리티
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

from app.core.config import settings

def setup_logging(
    level: str = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """
    로깅 설정 초기화
    """
    # 로그 레벨 설정
    log_level = level or settings.LOG_LEVEL
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 로그 포맷 설정
    if not format_string:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # 기본 설정
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        handlers=[]
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    
    # 루트 로거에 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (설정된 경우)
    if log_file:
        # 로그 디렉토리 생성
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    네임스페이스별 로거 반환
    """
    return logging.getLogger(name)

def log_request_info(
    method: str,
    url: str,
    user_id: Optional[int] = None,
    extra_info: Optional[dict] = None
) -> None:
    """
    API 요청 정보 로깅
    """
    logger = get_logger("api.request")
    
    info_parts = [f"{method} {url}"]
    
    if user_id:
        info_parts.append(f"user_id={user_id}")
    
    if extra_info:
        for key, value in extra_info.items():
            info_parts.append(f"{key}={value}")
    
    logger.info(" | ".join(info_parts))

def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict] = None
) -> None:
    """
    컨텍스트와 함께 에러 로깅
    """
    error_msg = f"Error: {type(error).__name__}: {str(error)}"
    
    if context:
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        error_msg += f" | Context: {context_str}"
    
    logger.error(error_msg, exc_info=True)

def log_performance(
    operation: str,
    duration_ms: float,
    success: bool = True,
    extra_info: Optional[dict] = None
) -> None:
    """
    성능 로깅
    """
    logger = get_logger("performance")
    
    status = "SUCCESS" if success else "FAILED"
    log_msg = f"{operation} | {status} | {duration_ms:.2f}ms"
    
    if extra_info:
        extra_str = ", ".join([f"{k}={v}" for k, v in extra_info.items()])
        log_msg += f" | {extra_str}"
    
    if success:
        logger.info(log_msg)
    else:
        logger.warning(log_msg)

class ContextLogger:
    """
    컨텍스트 정보가 포함된 로거
    """
    
    def __init__(self, logger: logging.Logger, context: dict):
        self.logger = logger
        self.context = context
    
    def _format_message(self, message: str) -> str:
        """메시지에 컨텍스트 정보 추가"""
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            return f"{message} | {context_str}"
        return message
    
    def debug(self, message: str) -> None:
        self.logger.debug(self._format_message(message))
    
    def info(self, message: str) -> None:
        self.logger.info(self._format_message(message))
    
    def warning(self, message: str) -> None:
        self.logger.warning(self._format_message(message))
    
    def error(self, message: str, exc_info: bool = False) -> None:
        self.logger.error(self._format_message(message), exc_info=exc_info)
    
    def critical(self, message: str) -> None:
        self.logger.critical(self._format_message(message))

def create_context_logger(name: str, **context) -> ContextLogger:
    """
    컨텍스트 로거 생성
    """
    logger = get_logger(name)
    return ContextLogger(logger, context) 