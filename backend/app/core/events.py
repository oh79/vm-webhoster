"""
애플리케이션 라이프사이클 이벤트
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.utils.logging_utils import setup_logging, get_logger

logger = get_logger("events")

async def create_tables():
    """
    데이터베이스 테이블 생성
    """
    try:
        # 동기 방식으로 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블이 생성되었습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 테이블 생성 실패: {e}")
        raise

async def check_database_connection():
    """
    데이터베이스 연결 확인
    """
    try:
        db = SessionLocal()
        # 간단한 쿼리로 연결 확인 (text() 사용)
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("데이터베이스 연결이 확인되었습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        raise

async def setup_vm_environment():
    """
    VM 환경 설정 확인
    """
    try:
        import subprocess
        
        # libvirt 연결 확인
        result = subprocess.run(
            ["virsh", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info(f"libvirt 버전: {result.stdout.strip()}")
        else:
            logger.warning("libvirt를 찾을 수 없습니다. VM 기능이 제한될 수 있습니다.")
        
        # VM 이미지 디렉토리 확인
        from pathlib import Path
        vm_image_path = Path(settings.VM_IMAGE_PATH)
        vm_image_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"VM 이미지 디렉토리: {vm_image_path}")
        
    except Exception as e:
        logger.warning(f"VM 환경 설정 확인 실패: {e}")

async def cleanup_temp_files():
    """
    임시 파일 정리
    """
    try:
        import tempfile
        import shutil
        from pathlib import Path
        
        temp_patterns = [
            "/tmp/vm-*.xml",
            "/tmp/*.qcow2"
        ]
        
        for pattern in temp_patterns:
            for file_path in Path("/tmp").glob(pattern):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.warning(f"임시 파일 삭제 실패 {file_path}: {e}")
        
        logger.info("임시 파일 정리가 완료되었습니다.")
        
    except Exception as e:
        logger.warning(f"임시 파일 정리 실패: {e}")

def startup_event():
    """
    애플리케이션 시작 이벤트
    """
    async def startup():
        logger.info(f"{settings.PROJECT_NAME} 애플리케이션이 시작됩니다...")
        
        # 로깅 설정
        setup_logging(
            level=settings.LOG_LEVEL,
            log_file=settings.LOG_FILE if hasattr(settings, 'LOG_FILE') else None
        )
        
        # 데이터베이스 초기화
        await create_tables()
        await check_database_connection()
        
        # VM 환경 설정
        await setup_vm_environment()
        
        # 임시 파일 정리
        await cleanup_temp_files()
        
        logger.info(f"{settings.PROJECT_NAME} 애플리케이션 시작이 완료되었습니다.")
    
    return startup

def shutdown_event():
    """
    애플리케이션 종료 이벤트
    """
    async def shutdown():
        logger.info(f"{settings.PROJECT_NAME} 애플리케이션을 종료합니다...")
        
        # 임시 파일 정리
        await cleanup_temp_files()
        
        # 데이터베이스 연결 정리
        try:
            engine.dispose()
            logger.info("데이터베이스 연결이 정리되었습니다.")
        except Exception as e:
            logger.error(f"데이터베이스 연결 정리 실패: {e}")
        
        logger.info(f"{settings.PROJECT_NAME} 애플리케이션 종료가 완료되었습니다.")
    
    return shutdown

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 0.93+ 스타일 라이프사이클 매니저
    """
    # 시작 이벤트
    await startup_event()()
    
    yield
    
    # 종료 이벤트
    await shutdown_event()()

def setup_event_handlers(app: FastAPI):
    """
    이벤트 핸들러 설정 (레거시 방식)
    """
    # FastAPI 0.93 이전 버전 호환
    app.add_event_handler("startup", startup_event())
    app.add_event_handler("shutdown", shutdown_event())
    
    logger.info("애플리케이션 이벤트 핸들러가 설정되었습니다.")

# 헬스체크 관련 함수들
async def perform_health_checks():
    """
    시스템 헬스체크 수행
    """
    health_status = {
        "database": False,
        "vm_system": False,
        "disk_space": False
    }
    
    # 데이터베이스 헬스체크
    try:
        await check_database_connection()
        health_status["database"] = True
    except Exception:
        pass
    
    # VM 시스템 헬스체크
    try:
        import subprocess
        result = subprocess.run(
            ["virsh", "list"],
            capture_output=True,
            timeout=5
        )
        health_status["vm_system"] = result.returncode == 0
    except Exception:
        pass
    
    # 디스크 공간 확인
    try:
        import shutil
        _, _, free = shutil.disk_usage("/")
        # 최소 1GB 여유 공간 필요
        health_status["disk_space"] = free > 1024 * 1024 * 1024
    except Exception:
        pass
    
    return health_status

# 백그라운드 작업 예시
async def background_cleanup_task():
    """
    백그라운드 정리 작업
    """
    while True:
        try:
            await cleanup_temp_files()
            # 1시간마다 실행
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"백그라운드 정리 작업 실패: {e}")
            await asyncio.sleep(300)  # 5분 후 재시도

async def start_background_tasks():
    """
    백그라운드 작업 시작
    """
    if not settings.DEBUG:  # 프로덕션 환경에서만 실행
        asyncio.create_task(background_cleanup_task())
        logger.info("백그라운드 작업이 시작되었습니다.") 