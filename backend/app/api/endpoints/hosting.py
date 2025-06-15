"""
호스팅 API 엔드포인트 - VM 기반 웹 호스팅 관리 (개선된 버전)
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.hosting import HostingStatus
from app.schemas.hosting import (
    HostingCreate, HostingResponse, HostingDetail, HostingUpdate,
    HostingOperation, HostingStats
)
from app.schemas.common import StandardResponse, PaginatedResponse
from app.utils.response_utils import (
    create_success_response,
    create_paginated_response,
    validate_pagination_params,
    calculate_offset
)
from app.utils.logging_utils import get_logger, log_request_info
from app.services.hosting_service import HostingService
from app.core.dependencies import get_current_user_id
from app.core.exceptions import (
    HostingNotFoundError, HostingAlreadyExistsError,
    VMOperationError, InsufficientPermissionError
)

# 라우터 설정
router = APIRouter(tags=["호스팅"])
logger = get_logger("api.hosting")

@router.post(
    "",
    response_model=StandardResponse[HostingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="호스팅 생성",
    description="새로운 VM 기반 호스팅을 생성합니다."
)
def create_hosting(
    hosting_data: HostingCreate,
    background_tasks: BackgroundTasks,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    호스팅 생성
    
    사용자당 1개의 호스팅만 생성할 수 있습니다.
    VM이 생성되는 동안 상태는 'creating'이며, 완료 후 'running' 상태로 변경됩니다.
    """
    log_request_info("POST", "/host", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        hosting = hosting_service.create_hosting(current_user_id, hosting_data)
        
        logger.info(f"호스팅 생성 시작: 사용자 {current_user_id}, 호스팅 {hosting.id}")
        
        return create_success_response(
            message="호스팅 생성이 시작되었습니다.",
            data=HostingResponse.model_validate(hosting)
        )
        
    except HostingAlreadyExistsError as e:
        logger.warning(f"호스팅 생성 실패 - 중복: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except VMOperationError as e:
        logger.error(f"호스팅 생성 실패 - VM 오류: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"호스팅 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 생성 중 오류가 발생했습니다."
        )

@router.get(
    "/my",
    response_model=StandardResponse[Optional[HostingResponse]],
    summary="내 호스팅 조회",
    description="현재 사용자의 호스팅을 조회합니다. 호스팅이 없으면 null을 반환합니다."
)
def get_my_hosting(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    내 호스팅 조회
    
    현재 사용자의 호스팅을 조회합니다.
    호스팅이 없는 경우 404 에러가 아닌 null을 반환합니다.
    """
    log_request_info("GET", "/hosting/my", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        hosting = hosting_service.get_hosting_by_user_id(current_user_id)
        
        if not hosting:
            logger.info(f"호스팅 없음: 사용자 {current_user_id}")
            return create_success_response(
                message="호스팅이 없습니다.",
                data=None
            )
        
        # 상태 동기화
        hosting = hosting_service.sync_hosting_status(hosting.id)
        
        hosting_response = HostingResponse.model_validate(hosting)
        
        logger.info(f"내 호스팅 조회: 사용자 {current_user_id}, 호스팅 {hosting.id}")
        
        return create_success_response(
            message="호스팅을 조회했습니다.",
            data=hosting_response
        )
        
    except Exception as e:
        logger.error(f"내 호스팅 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 조회 중 오류가 발생했습니다."
        )

@router.delete(
    "/my",
    response_model=StandardResponse[dict],
    summary="내 호스팅 삭제",
    description="현재 사용자의 호스팅을 삭제합니다."
)
def delete_my_hosting(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    내 호스팅 삭제
    
    현재 사용자의 호스팅을 완전히 삭제합니다.
    VM과 모든 데이터가 삭제되므로 주의하세요.
    """
    log_request_info("DELETE", "/hosting/my", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        hosting = hosting_service.get_hosting_by_user_id(current_user_id)
        
        if not hosting:
            raise HostingNotFoundError("호스팅을 찾을 수 없습니다.")
        
        # 호스팅 삭제
        success = hosting_service.delete_hosting(hosting.id, current_user_id)
        
        if success:
            logger.info(f"호스팅 삭제 완료: 사용자 {current_user_id}, 호스팅 {hosting.id}")
            
            return create_success_response(
                message="호스팅이 성공적으로 삭제되었습니다.",
                data={"deleted": True}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="호스팅 삭제에 실패했습니다."
            )
        
    except HostingNotFoundError as e:
        logger.warning(f"호스팅 삭제 실패: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except VMOperationError as e:
        logger.error(f"호스팅 삭제 실패 - VM 오류: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"호스팅 삭제 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 삭제 중 오류가 발생했습니다."
        )

@router.get(
    "/{hosting_id}",
    response_model=StandardResponse[HostingDetail],
    summary="호스팅 상세 조회",
    description="특정 호스팅의 상세 정보를 조회합니다."
)
def get_hosting(
    hosting_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    호스팅 상세 조회
    
    - **hosting_id**: 조회할 호스팅 ID
    
    본인의 호스팅만 조회할 수 있습니다.
    """
    log_request_info("GET", f"/hosting/{hosting_id}", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        hosting = hosting_service.get_hosting_with_details(hosting_id, current_user_id)
        
        # 상태 동기화
        hosting = hosting_service.sync_hosting_status(hosting_id)
        
        hosting_detail = HostingDetail.model_validate(hosting)
        
        logger.info(f"호스팅 상세 조회: 호스팅 {hosting_id}")
        
        return create_success_response(
            message="호스팅 상세 정보를 조회했습니다.",
            data=hosting_detail
        )
        
    except HostingNotFoundError as e:
        logger.warning(f"호스팅 상세 조회 실패: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except InsufficientPermissionError as e:
        logger.warning(f"호스팅 상세 조회 실패 - 권한 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"호스팅 상세 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 상세 조회 중 오류가 발생했습니다."
        )

@router.post(
    "/{hosting_id}/operations",
    response_model=StandardResponse[HostingResponse],
    summary="호스팅 운영 명령",
    description="호스팅 VM에 운영 명령을 실행합니다."
)
def perform_hosting_operation(
    hosting_id: int,
    operation: HostingOperation,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    호스팅 운영 명령 실행
    
    - **hosting_id**: 대상 호스팅 ID
    - **operation**: 실행할 명령 (start, stop, restart, delete)
    
    본인의 호스팅만 관리할 수 있습니다.
    """
    log_request_info(
        "POST", 
        f"/hosting/{hosting_id}/operations", 
        user_id=current_user_id,
        extra_info={"operation": operation.operation}
    )
    
    try:
        hosting_service = HostingService(db)
        
        # 운영 명령 실행
        result = hosting_service.perform_operation(
            hosting_id, 
            operation.operation, 
            current_user_id
        )
        
        if operation.operation == "delete" and result is None:
            logger.info(f"호스팅 삭제 완료: 호스팅 {hosting_id}")
            return create_success_response(
                message="호스팅이 삭제되었습니다.",
                data=None
            )
        
        logger.info(f"호스팅 운영 명령 실행: 호스팅 {hosting_id}, 명령 {operation.operation}")
        
        return create_success_response(
            message=f"호스팅 {operation.operation} 명령이 실행되었습니다.",
            data=HostingResponse.model_validate(result)
        )
        
    except HostingNotFoundError as e:
        logger.warning(f"호스팅 운영 명령 실패: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except InsufficientPermissionError as e:
        logger.warning(f"호스팅 운영 명령 실패 - 권한 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.detail
        )
    except VMOperationError as e:
        logger.error(f"호스팅 운영 명령 실패 - VM 오류: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"호스팅 운영 명령 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 운영 명령 실행 중 오류가 발생했습니다."
        )

@router.post(
    "/{hosting_id}/sync",
    response_model=StandardResponse[HostingResponse],
    summary="호스팅 상태 동기화",
    description="호스팅 상태를 실제 VM 상태와 동기화합니다."
)
def sync_hosting_status(
    hosting_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    호스팅 상태 동기화
    
    - **hosting_id**: 동기화할 호스팅 ID
    
    VM의 실제 상태를 확인하여 데이터베이스 상태를 업데이트합니다.
    """
    log_request_info("POST", f"/hosting/{hosting_id}/sync", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        
        # 권한 확인을 위해 먼저 호스팅 조회
        hosting = hosting_service.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        if hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 관리할 수 있습니다.")
        
        # 상태 동기화
        hosting = hosting_service.sync_hosting_status(hosting_id)
        
        logger.info(f"호스팅 상태 동기화: 호스팅 {hosting_id}, 상태 {hosting.status}")
        
        return create_success_response(
            message="호스팅 상태가 동기화되었습니다.",
            data=HostingResponse.model_validate(hosting)
        )
        
    except HostingNotFoundError as e:
        logger.warning(f"호스팅 상태 동기화 실패: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except InsufficientPermissionError as e:
        logger.warning(f"호스팅 상태 동기화 실패 - 권한 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"호스팅 상태 동기화 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 상태 동기화 중 오류가 발생했습니다."
        )

@router.get(
    "/all",
    response_model=PaginatedResponse[HostingResponse],
    summary="호스팅 목록 조회",
    description="호스팅 목록을 페이지네이션으로 조회합니다. (관리자 기능)"
)
def get_hostings(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    호스팅 목록 조회
    
    - **page**: 페이지 번호 (1부터 시작)
    - **size**: 페이지 크기 (1-100)
    
    현재는 모든 인증된 사용자가 조회 가능합니다. (관리자 기능)
    """
    log_request_info("GET", "/hosting/all", user_id=current_user_id, extra_info={"page": page, "size": size})
    
    try:
        # 페이지네이션 파라미터 검증
        pagination = validate_pagination_params(page, size)
        offset = calculate_offset(pagination.page, pagination.size)
        
        hosting_service = HostingService(db)
        hostings = hosting_service.get_all_hostings(skip=offset, limit=pagination.size)
        
        # 전체 호스팅 수 조회 (간단한 카운트)
        total_hostings = len(hosting_service.get_all_hostings(skip=0, limit=10000))  # 임시 방법
        
        # HostingResponse로 변환
        hosting_responses = [HostingResponse.model_validate(hosting) for hosting in hostings]
        
        logger.info(f"호스팅 목록 조회: 페이지 {page}, 크기 {size}, 전체 {total_hostings}개")
        
        return create_paginated_response(
            items=hosting_responses,
            total=total_hostings,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"호스팅 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 목록 조회 중 오류가 발생했습니다."
        )

@router.get(
    "/stats",
    response_model=StandardResponse[dict],
    summary="호스팅 통계 조회",
    description="호스팅 관련 통계 정보를 조회합니다."
)
def get_hosting_stats(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    호스팅 통계 조회
    
    현재 사용자의 호스팅 통계를 포함한 전체 통계 정보를 반환합니다.
    """
    log_request_info("GET", "/hosting/stats", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        
        # 사용자별 호스팅 조회
        user_hosting = hosting_service.get_hosting_by_user_id(current_user_id)
        
        # 전체 통계 조회 (향후 관리자 기능 확장 시 사용)
        stats = hosting_service.get_hosting_stats()
        
        # 사용자별 통계 구성
        user_stats = {
            "total_hostings": 1 if user_hosting else 0,
            "active_hostings": 1 if user_hosting and user_hosting.status == HostingStatus.RUNNING else 0,
            "status_breakdown": {
                "creating": 1 if user_hosting and user_hosting.status == HostingStatus.CREATING else 0,
                "running": 1 if user_hosting and user_hosting.status == HostingStatus.RUNNING else 0,
                "stopping": 1 if user_hosting and user_hosting.status == HostingStatus.STOPPING else 0,
                "stopped": 1 if user_hosting and user_hosting.status == HostingStatus.STOPPED else 0,
                "error": 1 if user_hosting and user_hosting.status == HostingStatus.ERROR else 0,
            }
        }
        
        logger.info(f"호스팅 통계 조회: 사용자 {current_user_id}")
        
        return create_success_response(
            message="호스팅 통계를 조회했습니다.",
            data=user_stats
        )
        
    except Exception as e:
        logger.error(f"호스팅 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 통계 조회 중 오류가 발생했습니다."
        )

@router.get(
    "/health/{hosting_id}",
    response_model=StandardResponse[Dict[str, Any]],
    summary="호스팅 헬스체크",
    description="호스팅의 상태를 점검하고 상세 정보를 조회합니다."
)
def check_hosting_health(
    hosting_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    호스팅 헬스체크
    
    VM 상태, 네트워크 연결성, SSH 접근성 등을 확인합니다.
    """
    log_request_info("GET", f"/host/health/{hosting_id}", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        health_status = hosting_service.perform_health_check(hosting_id)
        
        # 권한 확인 (호스팅 소유자만 조회 가능)
        hosting = hosting_service.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="호스팅을 찾을 수 없습니다."
            )
        
        if hosting.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 호스팅만 조회할 수 있습니다."
            )
        
        logger.info(f"호스팅 헬스체크 완료: 호스팅 ID {hosting_id}, 사용자 {current_user_id}")
        
        return create_success_response(
            message="호스팅 헬스체크가 완료되었습니다.",
            data=health_status
        )
        
    except HostingNotFoundError:
        logger.warning(f"헬스체크 실패 - 호스팅 없음: {hosting_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="호스팅을 찾을 수 없습니다."
        )
    except InsufficientPermissionError as e:
        logger.warning(f"헬스체크 실패 - 권한 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"호스팅 헬스체크 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="호스팅 헬스체크 중 오류가 발생했습니다."
        )

@router.get(
    "/ssh/{hosting_id}",
    response_model=StandardResponse[Dict[str, str]],
    summary="SSH 접속 정보 조회",
    description="호스팅의 SSH 접속에 필요한 정보를 조회합니다."
)
def get_hosting_ssh_info(
    hosting_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    SSH 접속 정보 조회
    
    SSH 키, 접속 명령어, 포트 정보 등을 제공합니다.
    """
    log_request_info("GET", f"/host/ssh/{hosting_id}", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        ssh_info = hosting_service.get_hosting_ssh_info(hosting_id, current_user_id)
        
        logger.info(f"SSH 정보 조회 완료: 호스팅 ID {hosting_id}, 사용자 {current_user_id}")
        
        return create_success_response(
            message="SSH 접속 정보를 조회했습니다.",
            data=ssh_info
        )
        
    except HostingNotFoundError:
        logger.warning(f"SSH 정보 조회 실패 - 호스팅 없음: {hosting_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="호스팅을 찾을 수 없습니다."
        )
    except InsufficientPermissionError as e:
        logger.warning(f"SSH 정보 조회 실패 - 권한 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.detail
        )
    except VMOperationError as e:
        logger.error(f"SSH 정보 조회 실패: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"SSH 정보 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSH 정보 조회 중 오류가 발생했습니다."
        )

@router.get(
    "/detailed/{hosting_id}",
    response_model=StandardResponse[Dict[str, Any]],
    summary="상세 호스팅 정보 조회",
    description="헬스 상태를 포함한 상세 호스팅 정보를 조회합니다."
)
def get_detailed_hosting_info(
    hosting_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    상세 호스팅 정보 조회
    
    기본 호스팅 정보와 헬스 상태를 함께 제공합니다.
    """
    log_request_info("GET", f"/host/detailed/{hosting_id}", user_id=current_user_id)
    
    try:
        hosting_service = HostingService(db)
        detailed_info = hosting_service.get_hosting_with_health_status(hosting_id, current_user_id)
        
        logger.info(f"상세 호스팅 정보 조회 완료: 호스팅 ID {hosting_id}, 사용자 {current_user_id}")
        
        return create_success_response(
            message="상세 호스팅 정보를 조회했습니다.",
            data=detailed_info
        )
        
    except HostingNotFoundError:
        logger.warning(f"상세 정보 조회 실패 - 호스팅 없음: {hosting_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="호스팅을 찾을 수 없습니다."
        )
    except InsufficientPermissionError as e:
        logger.warning(f"상세 정보 조회 실패 - 권한 없음: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"상세 호스팅 정보 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="상세 호스팅 정보 조회 중 오류가 발생했습니다."
        )

@router.get(
    "",
    response_model=StandardResponse[HostingResponse],
    summary="내 호스팅 조회",
    description="현재 사용자의 호스팅을 조회합니다."
)
def get_my_hosting_default(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    내 호스팅 조회 (기본 경로)
    
    /hosting/my와 동일한 기능입니다.
    """
    return get_my_hosting(current_user_id, db)

@router.get(
    "/host",
    response_model=StandardResponse[HostingResponse],
    summary="내 호스팅 조회 (host 경로)",
    description="현재 사용자의 호스팅을 조회합니다."
)
def get_my_hosting_host(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    내 호스팅 조회 (host 경로)
    
    /hosting/my와 동일한 기능을 /host 경로로 제공합니다.
    """
    return get_my_hosting(current_user_id, db)

@router.delete(
    "",
    response_model=StandardResponse[dict],
    summary="내 호스팅 삭제",
    description="현재 사용자의 호스팅을 삭제합니다."
)
def delete_my_hosting_default(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    내 호스팅 삭제 (기본 경로)
    
    /hosting/my와 동일한 기능입니다.
    """
    return delete_my_hosting(current_user_id, db) 