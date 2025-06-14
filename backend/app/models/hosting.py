"""
호스팅 모델 정의
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import BaseModel

class HostingStatus(PyEnum):
    """호스팅 상태 Enum"""
    CREATING = "creating"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class Hosting(BaseModel):
    """호스팅 모델"""
    __tablename__ = "hosting"
    
    # 사용자 관계 (1:N으로 변경 - 다중 호스팅 지원)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 호스팅 이름 (사용자가 지정 가능)
    name = Column(String(100), nullable=False, index=True)
    
    # VM 정보
    vm_id = Column(String(100), unique=True, nullable=False, index=True)
    vm_ip = Column(String(15), nullable=False)  # IPv4 주소
    ssh_port = Column(Integer, nullable=False, unique=True)
    
    # 호스팅 상태
    status = Column(Enum(HostingStatus), default=HostingStatus.CREATING, nullable=False)
    
    # 관계 설정
    user = relationship("User", back_populates="hosting")
    
    def __repr__(self):
        return f"<Hosting(id={self.id}, name='{self.name}', user_id={self.user_id}, vm_id='{self.vm_id}', status='{self.status.value}')>"
    
    @property
    def web_url(self):
        """웹 접속 URL 생성"""
        return f"http://localhost/{self.user_id}-{self.id}"  # 다중 호스팅 지원을 위해 수정
    
    @property
    def ssh_command(self):
        """SSH 접속 명령어 생성"""
        return f"ssh -p {self.ssh_port} user@localhost" 