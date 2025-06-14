"""
호스팅 서비스 - 호스팅 관련 비즈니스 로직 (개선된 버전)
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

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
    """호스팅 서비스 클래스 (개선된 버전)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vm_service = VMService()
        self.proxy_service = ProxyService()
    
    def create_hosting(self, user_id: int, hosting_data: HostingCreate) -> Hosting:
        """
        새 호스팅 생성 (개선된 버전 - 완전한 롤백 지원)
        """
        # 사용자 존재 확인
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError()
        
        # 기존 호스팅 확인 (사용자당 1개 제한)
        existing_hosting = self.db.query(Hosting).filter(Hosting.user_id == user_id).first()
        if existing_hosting:
            raise HostingAlreadyExistsError("이미 호스팅을 보유하고 있습니다.")
        
        # 생성된 리소스 추적
        created_resources = {
            'vm_id': None,
            'hosting_id': None,
            'ssh_port': None,
            'proxy_added': False,
            'vm_created': False
        }
        
        try:
            # VM ID 생성
            vm_id = self.vm_service.generate_vm_id()
            created_resources['vm_id'] = vm_id
            
            # 사용 가능한 SSH 포트 찾기
            ssh_port = self.vm_service.get_available_ssh_port()
            created_resources['ssh_port'] = ssh_port
            
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
            created_resources['hosting_id'] = hosting.id
            
            logger.info(f"호스팅 레코드 생성: 사용자 {user_id}, VM {vm_id}, 호스팅 ID {hosting.id}")
            
            try:
                # VM 생성 (웹서버 자동 설치 포함)
                logger.info(f"VM 생성 시작: {vm_id}")
                vm_result = self.vm_service.create_vm(vm_id, ssh_port, user_id=str(user_id))
                created_resources['vm_created'] = True
                
                # 호스팅 정보 업데이트
                hosting.vm_ip = vm_result["vm_ip"]
                hosting.status = HostingStatus.RUNNING  # 임시로 RUNNING 상태로 설정
                self.db.commit()
                
                logger.info(f"VM 생성 완료: {vm_id}, IP: {vm_result['vm_ip']}")
                
                try:
                    # 프록시 규칙 추가 (웹 접속 및 SSH 포워딩)
                    logger.info(f"프록시 규칙 추가 시작: 사용자 {user_id}")
                    proxy_result = self.proxy_service.add_proxy_rule(
                        user_id=str(user_id),
                        vm_ip=vm_result["vm_ip"],
                        ssh_port=ssh_port
                    )
                    created_resources['proxy_added'] = True
                    
                    # 호스팅 상태를 RUNNING으로 최종 확정
                    hosting.status = HostingStatus.RUNNING
                    self.db.commit()
                    self.db.refresh(hosting)
                    
                    logger.info(f"프록시 규칙 추가 완료: {proxy_result.get('web_url', 'N/A')}")
                    logger.info(f"호스팅 생성 완료: 사용자 {user_id}, VM {vm_id}")
                    
                    # 백그라운드에서 헬스체크 시작
                    self._schedule_health_check(hosting.id)
                    
                    return hosting
                    
                except Exception as proxy_error:
                    logger.error(f"프록시 설정 실패: {proxy_error}")
                    # 프록시 설정 실패 시 완전한 롤백
                    self._rollback_resources(created_resources)
                    raise VMOperationError(f"프록시 설정 실패: {proxy_error}")
                    
            except Exception as vm_error:
                logger.error(f"VM 생성 실패: {vm_error}")
                # VM 생성 실패 시 호스팅 상태 업데이트 후 롤백
                hosting.status = HostingStatus.ERROR
                self.db.commit()
                self._rollback_resources(created_resources)
                raise VMOperationError(f"VM 생성 실패: {vm_error}")
            
        except IntegrityError as e:
            logger.error(f"데이터베이스 무결성 오류: {e}")
            self.db.rollback()
            self._rollback_resources(created_resources)
            raise HostingAlreadyExistsError("호스팅 생성 중 중복 오류가 발생했습니다.")
            
        except Exception as e:
            logger.error(f"호스팅 생성 실패: {e}")
            self.db.rollback()
            self._rollback_resources(created_resources)
            raise VMOperationError(f"호스팅 생성 중 오류가 발생했습니다: {e}")
    
    def _rollback_resources(self, created_resources: Dict[str, Any]) -> None:
        """
        생성된 리소스들을 완전히 정리
        """
        logger.info(f"리소스 롤백 시작: {created_resources}")
        
        try:
            # 프록시 규칙 제거
            if created_resources.get('proxy_added') and created_resources.get('vm_id'):
                try:
                    # 사용자 ID를 추출하기 위해 호스팅 레코드에서 조회
                    if created_resources.get('hosting_id'):
                        hosting = self.db.query(Hosting).filter(
                            Hosting.id == created_resources['hosting_id']
                        ).first()
                        if hosting:
                            self.proxy_service.remove_proxy_rule(str(hosting.user_id))
                            logger.info(f"프록시 규칙 제거 완료: {hosting.user_id}")
                except Exception as e:
                    logger.error(f"프록시 규칙 제거 실패: {e}")
            
            # VM 삭제
            if created_resources.get('vm_created') and created_resources.get('vm_id'):
                try:
                    self.vm_service.delete_vm(created_resources['vm_id'])
                    logger.info(f"VM 삭제 완료: {created_resources['vm_id']}")
                except Exception as e:
                    logger.error(f"VM 삭제 실패: {e}")
            
            # 호스팅 레코드 삭제
            if created_resources.get('hosting_id'):
                try:
                    hosting = self.db.query(Hosting).filter(
                        Hosting.id == created_resources['hosting_id']
                    ).first()
                    if hosting:
                        self.db.delete(hosting)
                        self.db.commit()
                        logger.info(f"호스팅 레코드 삭제 완료: {created_resources['hosting_id']}")
                except Exception as e:
                    logger.error(f"호스팅 레코드 삭제 실패: {e}")
                    self.db.rollback()
                    
        except Exception as e:
            logger.error(f"리소스 롤백 중 오류: {e}")
    
    def _schedule_health_check(self, hosting_id: int) -> None:
        """
        헬스체크 스케줄링 (백그라운드 작업)
        """
        try:
            # 실제로는 백그라운드 작업 큐에 추가해야 함
            # 여기서는 로그만 남김
            logger.info(f"헬스체크 스케줄링: 호스팅 ID {hosting_id}")
            # TODO: Celery나 다른 백그라운드 작업 시스템과 연동
        except Exception as e:
            logger.error(f"헬스체크 스케줄링 실패: {e}")
    
    def perform_health_check(self, hosting_id: int) -> Dict[str, Any]:
        """
        호스팅 헬스체크 수행
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        health_status = {
            'hosting_id': hosting_id,
            'vm_id': hosting.vm_id,
            'vm_status': 'unknown',
            'web_accessible': False,
            'ssh_accessible': False,
            'last_check': datetime.utcnow().isoformat(),
            'issues': []
        }
        
        try:
            # VM 상태 확인
            vm_status = self.vm_service.get_vm_status(hosting.vm_id)
            health_status['vm_status'] = vm_status.value
            
            if vm_status != HostingStatus.RUNNING:
                health_status['issues'].append(f"VM 상태가 비정상입니다: {vm_status.value}")
                # 상태 동기화
                if hosting.status != vm_status:
                    hosting.status = vm_status
                    self.db.commit()
            
            # 웹 접근성 확인 (간단한 ping 테스트)
            try:
                import subprocess
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '3', hosting.vm_ip],
                    capture_output=True,
                    timeout=5
                )
                health_status['web_accessible'] = result.returncode == 0
                if result.returncode != 0:
                    health_status['issues'].append("VM에 ping이 실패했습니다")
            except Exception as e:
                health_status['issues'].append(f"네트워크 확인 실패: {e}")
            
            # SSH 포트 확인
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((hosting.vm_ip, hosting.ssh_port))
                health_status['ssh_accessible'] = result == 0
                sock.close()
                if result != 0:
                    health_status['issues'].append(f"SSH 포트 {hosting.ssh_port}에 연결할 수 없습니다")
            except Exception as e:
                health_status['issues'].append(f"SSH 포트 확인 실패: {e}")
            
            logger.info(f"헬스체크 완료: 호스팅 ID {hosting_id}, 이슈 {len(health_status['issues'])}개")
            
        except Exception as e:
            logger.error(f"헬스체크 수행 중 오류: {e}")
            health_status['issues'].append(f"헬스체크 수행 중 오류: {e}")
        
        return health_status
    
    def get_hosting_with_health_status(self, hosting_id: int, current_user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        호스팅 정보와 헬스 상태를 함께 조회
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        # 권한 확인 (필요한 경우)
        if current_user_id and hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 조회할 수 있습니다.")
        
        # 기본 호스팅 정보
        hosting_info = {
            'id': hosting.id,
            'user_id': hosting.user_id,
            'vm_id': hosting.vm_id,
            'vm_ip': hosting.vm_ip,
            'ssh_port': hosting.ssh_port,
            'status': hosting.status.value,
            'created_at': hosting.created_at.isoformat() if hosting.created_at else None,
            'updated_at': hosting.updated_at.isoformat() if hosting.updated_at else None,
            'web_url': hosting.web_url,
            'ssh_command': hosting.ssh_command
        }
        
        # 헬스체크 수행
        try:
            health_status = self.perform_health_check(hosting_id)
            hosting_info['health'] = health_status
        except Exception as e:
            logger.error(f"헬스체크 실패: {e}")
            hosting_info['health'] = {
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
        
        return hosting_info
    
    def get_hosting_ssh_info(self, hosting_id: int, current_user_id: int) -> Dict[str, str]:
        """
        호스팅의 SSH 접속 정보 조회 (개인키 포함)
        """
        hosting = self.get_hosting_by_id(hosting_id)
        if not hosting:
            raise HostingNotFoundError()
        
        # 권한 확인
        if hosting.user_id != current_user_id:
            raise InsufficientPermissionError("본인의 호스팅만 조회할 수 있습니다.")
        
        try:
            # SSH 개인키 파일 경로
            key_dir = self.vm_service.image_path / "ssh-keys" / hosting.vm_id
            private_key_file = key_dir / "id_rsa"
            public_key_file = key_dir / "id_rsa.pub"
            
            ssh_info = {
                'vm_id': hosting.vm_id,
                'vm_ip': hosting.vm_ip,
                'ssh_port': str(hosting.ssh_port),
                'username': 'ubuntu',
                'alternative_username': 'webhoster',
                'ssh_command': f"ssh -i id_rsa ubuntu@{hosting.vm_ip} -p {hosting.ssh_port}",
                'ssh_command_alt': f"ssh -i id_rsa webhoster@{hosting.vm_ip} -p {hosting.ssh_port}",
                'private_key': None,
                'public_key': None
            }
            
            # 개인키 읽기
            if private_key_file.exists():
                with open(private_key_file, 'r') as f:
                    ssh_info['private_key'] = f.read()
            
            # 공개키 읽기
            if public_key_file.exists():
                with open(public_key_file, 'r') as f:
                    ssh_info['public_key'] = f.read().strip()
            
            return ssh_info
            
        except Exception as e:
            logger.error(f"SSH 정보 조회 실패: {e}")
            raise VMOperationError(f"SSH 정보 조회 실패: {e}")
    
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
        호스팅 통계 조회 (개선된 버전)
        """
        try:
            # 전체 호스팅 수
            total_count = self.db.query(Hosting).count()
            
            # 상태별 호스팅 수
            status_counts = {}
            for status in HostingStatus:
                count = self.db.query(Hosting).filter(Hosting.status == status).count()
                status_counts[status.value] = count
            
            # 최근 생성된 호스팅 (지난 24시간)
            recent_threshold = datetime.utcnow() - timedelta(hours=24)
            recent_count = self.db.query(Hosting).filter(
                Hosting.created_at >= recent_threshold
            ).count()
            
            # 활성 호스팅 비율
            active_count = status_counts.get('running', 0)
            active_ratio = (active_count / total_count * 100) if total_count > 0 else 0
            
            return HostingStats(
                total_hostings=total_count,
                active_hostings=active_count,
                creating_hostings=status_counts.get('creating', 0),
                stopped_hostings=status_counts.get('stopped', 0),
                error_hostings=status_counts.get('error', 0),
                recent_hostings=recent_count,
                active_ratio=round(active_ratio, 2)
            )
            
        except Exception as e:
            logger.error(f"호스팅 통계 조회 실패: {e}")
            # 기본값 반환
            return HostingStats(
                total_hostings=0,
                active_hostings=0,
                creating_hostings=0,
                stopped_hostings=0,
                error_hostings=0,
                recent_hostings=0,
                active_ratio=0.0
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