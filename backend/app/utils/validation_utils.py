"""
데이터 검증 유틸리티
"""
import re
from typing import Optional, Any, List, Dict
from pydantic import ValidationError

def is_valid_email(email: str) -> bool:
    """
    이메일 주소 유효성 검증
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_username(username: str) -> bool:
    """
    사용자명 유효성 검증
    - 2-50자 길이
    - 영문, 숫자, 언더스코어, 하이픈만 허용
    """
    if not username or len(username) < 2 or len(username) > 50:
        return False
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, username))

def is_valid_vm_id(vm_id: str) -> bool:
    """
    VM ID 유효성 검증
    - vm- 접두사로 시작
    - 영문소문자, 숫자, 하이픈만 허용
    """
    if not vm_id or not vm_id.startswith('vm-'):
        return False
    
    pattern = r'^vm-[a-z0-9-]+$'
    return bool(re.match(pattern, vm_id))

def is_valid_port(port: int) -> bool:
    """
    포트 번호 유효성 검증
    """
    return 1 <= port <= 65535

def is_valid_ip_address(ip: str) -> bool:
    """
    IP 주소 유효성 검증 (IPv4)
    """
    if not ip:
        return False
    
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))

def sanitize_string(value: str, max_length: int = 255, allowed_chars: Optional[str] = None) -> str:
    """
    문자열 정제
    """
    if not isinstance(value, str):
        value = str(value)
    
    # HTML 태그 제거
    value = re.sub(r'<[^>]+>', '', value)
    
    # 특수 문자 제거 (허용된 문자만 남김)
    if allowed_chars:
        pattern = f'[^{re.escape(allowed_chars)}]'
        value = re.sub(pattern, '', value)
    
    # 길이 제한
    value = value[:max_length]
    
    # 앞뒤 공백 제거
    return value.strip()

def validate_positive_integer(value: Any, field_name: str = "값") -> int:
    """
    양의 정수 검증
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError(f"{field_name}은(는) 양의 정수여야 합니다.")
        return int_value
    except (ValueError, TypeError):
        raise ValueError(f"{field_name}은(는) 유효한 정수여야 합니다.")

def validate_range(value: int, min_val: int, max_val: int, field_name: str = "값") -> int:
    """
    범위 검증
    """
    if not min_val <= value <= max_val:
        raise ValueError(f"{field_name}은(는) {min_val}과 {max_val} 사이의 값이어야 합니다.")
    return value

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    필수 필드 검증
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}")

def validate_pydantic_model(model_class, data: Dict[str, Any]) -> Any:
    """
    Pydantic 모델 검증
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append(f"{field}: {message}")
        
        raise ValueError(f"데이터 검증 실패: {'; '.join(errors)}")

def clean_filename(filename: str) -> str:
    """
    파일명 정제 (안전한 파일명으로 변환)
    """
    if not filename:
        return "untitled"
    
    # 위험한 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # 연속된 공백을 하나로
    filename = re.sub(r'\s+', ' ', filename)
    
    # 앞뒤 공백 및 점 제거
    filename = filename.strip(' .')
    
    # 빈 문자열인 경우 기본값
    if not filename:
        filename = "untitled"
    
    # 길이 제한 (255자)
    return filename[:255]

def is_safe_path(path: str, base_path: str = "/") -> bool:
    """
    경로 안전성 검증 (디렉토리 트래버설 공격 방지)
    """
    import os.path
    
    # 절대 경로로 변환
    abs_path = os.path.abspath(path)
    abs_base = os.path.abspath(base_path)
    
    # 기본 경로 내에 있는지 확인
    return abs_path.startswith(abs_base)

class ValidationResult:
    """검증 결과를 담는 클래스"""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, error: str) -> None:
        """에러 추가"""
        self.errors.append(error)
        self.is_valid = False
    
    def get_error_message(self) -> str:
        """에러 메시지 문자열로 반환"""
        return "; ".join(self.errors) if self.errors else "" 