#!/usr/bin/env python3
"""
nginx 자동화 테스트 스크립트
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def test_proxy_automation():
    """프록시 자동화 테스트"""
    print("🚀 nginx 프록시 자동화 테스트 시작")
    
    # 프로젝트 루트 경로
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 백엔드 환경 활성화
    try:
        # ProxyService 테스트
        sys.path.append(str(project_root / "backend"))
        
        # 환경 변수 설정
        os.environ["NGINX_CONFIG_PATH"] = str(project_root / "backend" / "nginx-configs")
        os.environ["SERVICE_DOMAIN"] = "localhost"
        
        from app.services.proxy_service import ProxyService
        
        # ProxyService 인스턴스 생성
        proxy_service = ProxyService()
        
        # 테스트용 사용자 데이터
        test_users = [
            {"user_id": "11", "vm_ip": "127.0.0.1", "ssh_port": 10028, "web_port": 8555},
            {"user_id": "12", "vm_ip": "127.0.0.1", "ssh_port": 10029, "web_port": 8556}
        ]
        
        print(f"\n📋 {len(test_users)}명의 테스트 사용자로 자동화 테스트")
        
        success_count = 0
        
        for user_data in test_users:
            user_id = user_data["user_id"]
            print(f"\n🔧 사용자 {user_id} 프록시 설정 생성 중...")
            
            try:
                # 프록시 규칙 추가
                result = proxy_service.add_proxy_rule(
                    user_id=user_id,
                    vm_ip=user_data["vm_ip"],
                    ssh_port=user_data["ssh_port"],
                    web_port=user_data["web_port"]
                )
                
                if result.get("nginx_applied", False):
                    print(f"✅ 사용자 {user_id} 자동 적용 성공!")
                    print(f"   웹 URL: {result['web_url']}")
                    print(f"   SSH: {result['ssh_command']}")
                    success_count += 1
                else:
                    print(f"⚠️ 사용자 {user_id} 설정 파일만 생성됨")
                    print(f"   수동 명령: {result.get('manual_command', 'N/A')}")
                
                # 설정 상태 확인
                status = proxy_service.get_proxy_status(user_id)
                print(f"   설정 상태: {'✅' if status.get('nginx_enabled', False) else '❌'}")
                
            except Exception as e:
                print(f"❌ 사용자 {user_id} 설정 실패: {e}")
        
        # 결과 요약
        print(f"\n📊 자동화 테스트 결과:")
        print(f"   총 사용자: {len(test_users)}명")
        print(f"   자동 적용 성공: {success_count}명")
        print(f"   성공률: {success_count/len(test_users)*100:.1f}%")
        
        # 활성 프록시 목록 조회
        active_proxies = proxy_service.list_active_proxies()
        print(f"\n🌐 현재 활성 프록시: {len(active_proxies)}개")
        for proxy in active_proxies[-5:]:  # 최근 5개만 표시
            print(f"   - 사용자 {proxy['user_id']}: {proxy['web_url']}")
        
        return success_count == len(test_users)
        
    except ImportError as e:
        print(f"❌ 백엔드 모듈 로드 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return False

def cleanup_test_users():
    """테스트 사용자 정리"""
    print("\n🧹 테스트 사용자 정리 중...")
    
    test_user_ids = ["11", "12"]
    project_root = Path(__file__).parent.parent
    
    for user_id in test_user_ids:
        try:
            # 스크립트를 통한 정리
            script_path = project_root / "scripts" / "remove_nginx_config.sh"
            if script_path.exists():
                result = subprocess.run(
                    ["bash", str(script_path), user_id],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(project_root)
                )
                
                if result.returncode == 0:
                    print(f"✅ 사용자 {user_id} 정리 완료")
                else:
                    print(f"⚠️ 사용자 {user_id} 정리 실패: {result.stderr}")
            
        except Exception as e:
            print(f"❌ 사용자 {user_id} 정리 중 오류: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 nginx 프록시 자동화 시스템 테스트")
    print("=" * 60)
    
    try:
        # 자동화 테스트 실행
        test_success = test_proxy_automation()
        
        if test_success:
            print("\n🎉 자동화 테스트 완전 성공!")
            print("   새로운 사용자가 생성되면 자동으로 nginx 설정이 적용됩니다.")
        else:
            print("\n⚠️ 자동화 테스트 부분 성공")
            print("   일부 설정이 수동으로 적용되어야 할 수 있습니다.")
        
        # 테스트 사용자 정리
        cleanup_test_users()
        
        print("\n📝 결론:")
        print("   - 백엔드에서 ProxyService.add_proxy_rule() 호출 시 자동 적용")
        print("   - 스크립트를 통한 sudo 권한 nginx 설정 관리")
        print("   - webhosting 파일 수정 없이 개별 설정 파일 방식 사용")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 테스트 중단됨")
        cleanup_test_users()
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 치명적 오류: {e}")
        cleanup_test_users()
    
    print("\n" + "=" * 60) 