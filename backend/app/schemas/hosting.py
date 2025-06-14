"""
호스팅 관련 Pydantic 스키마
"""
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.hosting import HostingStatus
from app.schemas.user import UserResponse

class HostingBase(BaseModel):
    """호스팅 기본 정보"""
    pass

class HostingCreate(HostingBase):
    """호스팅 생성 요청 (사용자는 자동으로 현재 로그인 사용자)"""
    pass

class HostingUpdate(BaseModel):
    """호스팅 상태 업데이트"""
    status: HostingStatus = Field(..., description="호스팅 상태")

class HostingResponse(BaseModel):
    """호스팅 기본 응답"""
    id: int = Field(..., description="호스팅 ID")
    user_id: int = Field(..., description="사용자 ID")
    vm_id: str = Field(..., description="VM ID")
    vm_ip: str = Field(..., description="VM IP 주소")
    ssh_port: int = Field(..., description="SSH 포트")
    status: HostingStatus = Field(..., description="호스팅 상태")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    
    model_config = {"from_attributes": True}

class HostingDetail(HostingResponse):
    """호스팅 상세 정보 (사용자 정보 포함)"""
    user: UserResponse = Field(..., description="사용자 정보")
    web_url: str = Field(..., description="웹 접속 URL")
    ssh_command: str = Field(..., description="SSH 접속 명령어")
    
    @field_validator('web_url', mode='before')
    @classmethod
    def set_web_url(cls, v, info):
        if info.data and 'vm_id' in info.data:
            return f"http://localhost/{info.data['vm_id']}"
        return v
    
    @field_validator('ssh_command', mode='before')
    @classmethod
    def set_ssh_command(cls, v, info):
        if info.data and 'ssh_port' in info.data:
            return f"ssh -p {info.data['ssh_port']} user@localhost"
        return v

class HostingStats(BaseModel):
    """호스팅 통계 (개선된 버전)"""
    total_hostings: int = Field(..., description="전체 호스팅 수")
    active_hostings: int = Field(..., description="활성 호스팅 수")
    creating_hostings: int = Field(..., description="생성 중인 호스팅 수")
    stopped_hostings: int = Field(..., description="중지된 호스팅 수")
    error_hostings: int = Field(..., description="오류 상태 호스팅 수")
    recent_hostings: int = Field(..., description="최근 24시간 생성된 호스팅 수")
    active_ratio: float = Field(..., description="활성 호스팅 비율 (%)")

class HostingHealth(BaseModel):
    """호스팅 헬스체크 결과"""
    hosting_id: int = Field(..., description="호스팅 ID")
    vm_id: str = Field(..., description="VM ID")
    vm_status: str = Field(..., description="VM 상태")
    web_accessible: bool = Field(..., description="웹 접근 가능 여부")
    ssh_accessible: bool = Field(..., description="SSH 접근 가능 여부")
    last_check: str = Field(..., description="마지막 확인 시간")
    issues: List[str] = Field(default=[], description="발견된 문제점 목록")

class SSHInfo(BaseModel):
    """SSH 접속 정보"""
    vm_id: str = Field(..., description="VM ID")
    vm_ip: str = Field(..., description="VM IP 주소")
    ssh_port: str = Field(..., description="SSH 포트")
    username: str = Field(..., description="기본 사용자명")
    alternative_username: str = Field(..., description="대체 사용자명")
    ssh_command: str = Field(..., description="SSH 접속 명령어")
    ssh_command_alt: str = Field(..., description="대체 SSH 접속 명령어")
    private_key: Optional[str] = Field(None, description="SSH 개인키")
    public_key: Optional[str] = Field(None, description="SSH 공개키")

class DetailedHostingInfo(BaseModel):
    """상세 호스팅 정보"""
    id: int = Field(..., description="호스팅 ID")
    user_id: int = Field(..., description="사용자 ID")
    vm_id: str = Field(..., description="VM ID")
    vm_ip: str = Field(..., description="VM IP 주소")
    ssh_port: int = Field(..., description="SSH 포트")
    status: str = Field(..., description="호스팅 상태")
    created_at: Optional[str] = Field(None, description="생성 시간")
    updated_at: Optional[str] = Field(None, description="수정 시간")
    web_url: str = Field(..., description="웹 접속 URL")
    ssh_command: str = Field(..., description="SSH 접속 명령어")
    health: Optional[Union[HostingHealth, Dict[str, Any]]] = Field(None, description="헬스체크 결과")

class VMInfo(BaseModel):
    """VM 정보"""
    vm_id: str = Field(..., description="VM ID")
    vm_ip: str = Field(..., description="VM IP")
    ssh_port: int = Field(..., description="SSH 포트")
    status: HostingStatus = Field(..., description="VM 상태")
    web_url: str = Field(..., description="웹 접속 URL")
    ssh_command: str = Field(..., description="SSH 접속 명령어")
    
class HostingOperation(BaseModel):
    """호스팅 운영 명령"""
    operation: str = Field(..., description="운영 명령 (start, stop, restart, delete)")
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v):
        allowed_operations = ['start', 'stop', 'restart', 'delete']
        if v not in allowed_operations:
            raise ValueError(f'허용되지 않은 운영 명령입니다. 허용된 명령: {", ".join(allowed_operations)}')
        return v 