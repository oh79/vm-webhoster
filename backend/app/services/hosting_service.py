"""
호스팅 서비스 - 호스팅 관련 비즈니스 로직
"""
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.hosting import Hosting, HostingStatus
from app.models.user import User
from app.schemas.hosting import HostingCreate, HostingUpdate, HostingStats
from app.services.vm_service import VMService
from app.services.proxy_service import ProxyService
from app.core.exceptions import (
    HostingNotFoundError,
    HostingAlreadyExistsError,
    VMOperationError,
    InsufficientPermissionError,
    UserNotFoundError
)

# 로깅 설정
logger = logging.getLogger(__name__)

class HostingService:
    """호스팅 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vm_service = VMService()
        self.proxy_service = ProxyService()
    
    def create_hosting(self, user_id: int, hosting_data: HostingCreate) -> Hosting:
        """
        새 호스팅 생성 (프록시 규칙 자동 추가 포함)
        """
        # 사용자 존재 확인
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError()
        
        # 기존 호스팅 확인 (사용자당 1개 제한)
        existing_hosting = self.db.query(Hosting).filter(Hosting.user_id == user_id).first()
        if existing_hosting:
            raise HostingAlreadyExistsError("이미 호스팅을 보유하고 있습니다.")
        
        vm_id = None
        hosting = None
        
        try:
            # VM ID 생성
            vm_id = self.vm_service.generate_vm_id()
            
            # 사용 가능한 SSH 포트 찾기
            ssh_port = self.vm_service.get_available_ssh_port()
            
            # 호스팅 레코드 생성 (상태: CREATING)
            hosting = Hosting(
                user_id=user_id,
                vm_id=vm_id,
                vm_ip="0.0.0.0",  # VM 생성 후 업데이트
                ssh_port=ssh_port,
                status=HostingStatus.CREATING
            )
            
            self.db.add(hosting)
            self.db.commit()
            self.db.refresh(hosting)
            
            logger.info(f"호스팅 레코드 생성: 사용자 {user_id}, VM {vm_id}")
            
            try:
                # VM 생성 (웹서버 자동 설치 포함)
                vm_result = self.vm_service.create_vm(vm_id, ssh_port, user_id=str(user_id))
                
                # 호스팅 정보 업데이트
                hosting.vm_ip = vm_result["vm_ip"]
                self.db.commit()
                
                logger.info(f"VM 생성 완료: {vm_id}, IP: {vm_result['vm_ip']}")
                
                try:
                    # 프록시 규칙 추가 (웹 접속 및 SSH 포워딩)
                    proxy_result = self.proxy_service.add_proxy_rule(
                        user_id=str(user_id),
                        vm_ip=vm_result["vm_ip"],
                        ssh_port=ssh_port
                    )
                    
                    # 호스팅 상태를 RUNNING으로 변경
                    hosting.status = HostingStatus.RUNNING
                    self.db.commit()
                    self.db.refresh(hosting)
                    
                    logger.info(f"프록시 규칙 추가 완료: {proxy_result['web_url']}")
                    logger.info(f"호스팅 생성 완료: 사용자 {user_id}, VM {vm_id}")
                    
                except Exception as proxy_error:
                    # 프록시 설정 실패 시 VM 삭제 (롤백)
                    logger.error(f"프록시 설정 실패, VM 삭제 진행: {proxy_error}")
                    
                    try:
                        self.vm_service.delete_vm(vm_id)
                        logger.info(f"프록시 실패로 인한 VM 삭제 완료: {vm_id}")
                    except Exception as vm_delete_error:
                        logger.error(f"VM 삭제 실패: {vm_delete_error}")
                    
                    # 호스팅 상태를 ERROR로 변경
                    hosting.status = HostingStatus.ERROR
                    self.db.commit()
                    
                    raise VMOperationError(f"프록시 설정 실패: {proxy_error}")
                    
            except VMOperationError as vm_error:
                # VM 생성 실패 시 호스팅 상태 업데이트
                hosting.status = HostingStatus.ERROR
                self.db.commit()
                logger.error(f"VM 생성 실패: {vm_error}")
                raise vm_error
            
            return hosting
            
        except IntegrityError:
            self.db.rollback()
            # 생성된 리소스 정리
            if vm_id:
                try:
                    self.vm_service.delete_vm(vm_id)
                    logger.info(f"롤백: VM 삭제 완료 {vm_id}")
                except Exception as e:
                    logger.error(f"롤백 중 VM 삭제 실패: {e}")
            raise HostingAlreadyExistsError("호스팅 생성 중 중복 오류가 발생했습니다.")
        except Exception as e:
            self.db.rollback()
            # 생성된 리소스 정리
            if vm_id:
                try:
                    self.vm_service.delete_vm(vm_id)
                    self.proxy_service.remove_proxy_rule(str(user_id))
                    logger.info(f"롤백: 리소스 정리 완료 {vm_id}")
                except Exception as cleanup_error:
                    logger.error(f"롤백 중 리소스 정리 실패: {cleanup_error}")
            
            logger.error(f"호스팅 생성 실패: {e}")
            raise VMOperationError(f"호스팅 생성 중 오류가 발생했습니다: {e}")
    
    def get_hosting_by_id(self, hosting_id: int) -> Optional[Hosting]:
        """
        ID로 호스팅 조회
        """
        return self.db.query(Hosting).filter(Hosting.id == hosting_id).first()
    
    def get_hosting_by_user_id(self, user_id: int) -> Optional[Hosting]:
        """
        사용자 ID로 호스팅 조회
        """
        return self.db.query(Hosting).filter(Hosting.user_id == user_id).first()
    
    def get_hosting_by_vm_id(self, vm_id: str) -> Optional[Hosting]:
        """
        VM ID로 호스팅 조회
        """
        return self.db.query(Hosting).filter(Hosting.vm_id == vm_id).first()
    
    def get_user_hostings(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Hosting]:
        """
        사용자의 호스팅 목록 조회
        """
        return (
            self.db.query(Hosting)
            .filter(Hosting.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_all_hostings(self, skip: int = 0, limit: int = 100) -> List[Hosting]:
        """
        모든 호스팅 목록 조회 (관리자용)
        """
        return self.db.query(Hosting).offset(skip).limit(limit).all()
    
    def update_hosting_status(self, hosting_id: int, status: HostingStatus, current_user_id: int) -> Hosting:
        """
        호스팅 상태 업데이트
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        # 권한 확인 (본인의 호스팅만 수정 가능)
        if hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 관리할 수 있습니다.")
        
        hosting.status = status
        self.db.commit()
        self.db.refresh(hosting)
        
        return hosting
    
    def start_hosting(self, hosting_id: int, current_user_id: int) -> Hosting:
        """
        호스팅 시작
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        # 권한 확인
        if hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 관리할 수 있습니다.")
        
        try:
            # VM 시작
            success = self.vm_service.start_vm(hosting.vm_id)
            
            if success:
                hosting.status = HostingStatus.RUNNING
                self.db.commit()
                self.db.refresh(hosting)
                
                logger.info(f"호스팅 시작: {hosting_id}")
            
            return hosting
            
        except VMOperationError as e:
            hosting.status = HostingStatus.ERROR
            self.db.commit()
            raise e
    
    def stop_hosting(self, hosting_id: int, current_user_id: int) -> Hosting:
        """
        호스팅 중지
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        # 권한 확인
        if hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 관리할 수 있습니다.")
        
        try:
            # VM 중지
            success = self.vm_service.stop_vm(hosting.vm_id)
            
            if success:
                hosting.status = HostingStatus.STOPPING
                self.db.commit()
                self.db.refresh(hosting)
                
                logger.info(f"호스팅 중지: {hosting_id}")
            
            return hosting
            
        except VMOperationError as e:
            hosting.status = HostingStatus.ERROR
            self.db.commit()
            raise e
    
    def restart_hosting(self, hosting_id: int, current_user_id: int) -> Hosting:
        """
        호스팅 재시작
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        # 권한 확인
        if hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 관리할 수 있습니다.")
        
        try:
            # VM 재시작
            success = self.vm_service.restart_vm(hosting.vm_id)
            
            if success:
                hosting.status = HostingStatus.RUNNING
                self.db.commit()
                self.db.refresh(hosting)
                
                logger.info(f"호스팅 재시작: {hosting_id}")
            
            return hosting
            
        except VMOperationError as e:
            hosting.status = HostingStatus.ERROR
            self.db.commit()
            raise e
    
    def delete_hosting(self, hosting_id: int, current_user_id: int) -> bool:
        """
        호스팅 삭제
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        # 권한 확인
        if hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 삭제할 수 있습니다.")
        
        try:
            # VM 삭제
            success = self.vm_service.delete_vm(hosting.vm_id)
            
            if success:
                # 데이터베이스에서 호스팅 레코드 삭제
                self.db.delete(hosting)
                self.db.commit()
                
                logger.info(f"호스팅 삭제 완료: {hosting_id}")
                return True
            
            return False
            
        except VMOperationError as e:
            logger.error(f"호스팅 삭제 실패: {e}")
            raise e
    
    def delete_hosting_by_user_id(self, user_id: int) -> bool:
        """
        사용자 ID로 호스팅 삭제
        """
        hosting = self.get_hosting_by_user_id(user_id)
        if not hosting:
            raise HostingNotFoundError("호스팅을 찾을 수 없습니다.")
        
        return self.delete_hosting(hosting.id, user_id)
    
    def sync_hosting_status(self, hosting_id: int) -> Hosting:
        """
        VM 상태와 호스팅 상태 동기화
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        try:
            # VM 상태 조회
            vm_status = self.vm_service.get_vm_status(hosting.vm_id)
            
            # 호스팅 상태 업데이트
            if hosting.status != vm_status:
                hosting.status = vm_status
                self.db.commit()
                self.db.refresh(hosting)
                
                logger.info(f"호스팅 상태 동기화: {hosting_id} -> {vm_status}")
            
            return hosting
            
        except Exception as e:
            logger.error(f"호스팅 상태 동기화 실패: {e}")
            hosting.status = HostingStatus.ERROR
            self.db.commit()
            return hosting
    
    def get_hosting_stats(self) -> HostingStats:
        """
        호스팅 통계 조회
        """
        total_hostings = self.db.query(Hosting).count()
        active_hostings = self.db.query(Hosting).filter(Hosting.status == HostingStatus.RUNNING).count()
        creating_hostings = self.db.query(Hosting).filter(Hosting.status == HostingStatus.CREATING).count()
        error_hostings = self.db.query(Hosting).filter(Hosting.status == HostingStatus.ERROR).count()
        
        return HostingStats(
            total_hostings=total_hostings,
            active_hostings=active_hostings,
            creating_hostings=creating_hostings,
            error_hostings=error_hostings
        )
    
    def get_hosting_with_details(self, hosting_id: int, current_user_id: Optional[int] = None) -> Hosting:
        """
        호스팅 상세 정보 조회 (사용자 정보 포함)
        """
        hosting = (
            self.db.query(Hosting)
            .join(User)
            .filter(Hosting.id == hosting_id)
            .first()
        )
        
        if not hosting:
            raise HostingNotFoundError()
        
        # 권한 확인 (본인의 호스팅만 조회 가능)
        if current_user_id and hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 조회할 수 있습니다.")
        
        return hosting
    
    def perform_operation(self, hosting_id: int, operation: str, current_user_id: int) -> Hosting:
        """
        호스팅 운영 명령 실행
        """
        operation_map = {
            'start': self.start_hosting,
            'stop': self.stop_hosting,
            'restart': self.restart_hosting,
        }
        
        if operation == 'delete':
            success = self.delete_hosting(hosting_id, current_user_id)
            if success:
                return None  # 삭제된 경우 None 반환
        
        if operation not in operation_map:
            raise VMOperationError(f"지원되지 않는 운영 명령입니다: {operation}")
        
        return operation_map[operation](hosting_id, current_user_id) 