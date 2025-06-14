#!/usr/bin/env python3
"""
웹 호스팅 서비스를 위한 Nginx 설정 스크립트
과제 요구사항에 따른 사용자별 URL 라우팅 구현
"""

import os
import sys
from pathlib import Path

def create_nginx_config():
    """기본 Nginx 설정 파일 생성"""
    
    # Nginx 설정 디렉토리
    nginx_dir = Path("/etc/nginx")
    sites_available = nginx_dir / "sites-available"
    sites_enabled = nginx_dir / "sites-enabled"
    
    # 웹 호스팅 서비스 설정 파일
    config_content = """# 웹 호스팅 서비스 기본 설정
server {
    listen 80 default_server;
    server_name localhost _;
    
    # 메인 페이지
    location = / {
        return 200 '
        <!DOCTYPE html>
        <html>
        <head>
            <title>웹 호스팅 서비스</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container { 
                    background: rgba(255,255,255,0.1); 
                    padding: 30px; 
                    border-radius: 10px; 
                    display: inline-block;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 웹 호스팅 서비스</h1>
                <p>사용자별 접속: /&lt;user_id&gt;</p>
                <p>예: /7 (사용자 ID가 7인 경우)</p>
            </div>
        </body>
        </html>';
        add_header Content-Type text/html;
    }
    
    # 사용자별 호스팅 설정은 동적으로 추가됩니다
    # 예: location /7 { proxy_pass http://127.0.0.1:8XXX; }
}
"""
    
    try:
        # 로컬 nginx 설정 디렉토리 생성
        local_nginx_dir = Path("nginx-configs")
        local_nginx_dir.mkdir(exist_ok=True)
        
        # 설정 파일 저장
        config_file = local_nginx_dir / "webhosting.conf"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ Nginx 설정 파일 생성: {config_file}")
        
        # 시스템 Nginx 설정에 복사 (권한이 있는 경우)
        if nginx_dir.exists() and os.access(nginx_dir, os.W_OK):
            system_config = sites_available / "webhosting"
            with open(system_config, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # sites-enabled에 링크 생성
            enabled_link = sites_enabled / "webhosting"
            if not enabled_link.exists():
                enabled_link.symlink_to(system_config)
                
            print(f"✅ 시스템 Nginx 설정 업데이트: {system_config}")
            print("⚠️  Nginx 재시작 필요: sudo systemctl reload nginx")
        else:
            print("⚠️  시스템 Nginx 설정 권한 없음. 수동으로 복사하세요:")
            print(f"   sudo cp {config_file} /etc/nginx/sites-available/webhosting")
            print(f"   sudo ln -s /etc/nginx/sites-available/webhosting /etc/nginx/sites-enabled/")
            print(f"   sudo nginx -t && sudo systemctl reload nginx")
        
        return True
        
    except Exception as e:
        print(f"❌ Nginx 설정 실패: {e}")
        return False

def setup_docker_environment():
    """Docker 환경 설정"""
    try:
        # Docker 설치 확인
        import subprocess
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker 설치됨: {result.stdout.strip()}")
        else:
            print("❌ Docker가 설치되지 않았습니다.")
            print("   설치 방법: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh")
            return False
            
        # 필요한 Docker 이미지 확인
        images_to_pull = ["nginx:alpine"]
        for image in images_to_pull:
            print(f"🐳 Docker 이미지 확인: {image}")
            pull_result = subprocess.run(["docker", "pull", image], 
                                       capture_output=True, text=True)
            if pull_result.returncode == 0:
                print(f"✅ 이미지 준비됨: {image}")
            else:
                print(f"❌ 이미지 다운로드 실패: {image}")
                
        return True
        
    except Exception as e:
        print(f"❌ Docker 환경 설정 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 웹 호스팅 서비스 설정 시작...")
    
    # 1. Nginx 설정
    print("\n1. Nginx 설정")
    nginx_ok = create_nginx_config()
    
    # 2. Docker 환경 설정
    print("\n2. Docker 환경 설정")
    docker_ok = setup_docker_environment()
    
    # 결과 요약
    print("\n" + "="*50)
    print("📋 설정 완료 상태:")
    print(f"   Nginx 설정: {'✅' if nginx_ok else '❌'}")
    print(f"   Docker 환경: {'✅' if docker_ok else '❌'}")
    
    if nginx_ok and docker_ok:
        print("\n🎉 웹 호스팅 서비스 환경 설정 완료!")
        print("   서버를 시작하고 호스팅을 생성해보세요.")
    else:
        print("\n⚠️  일부 설정이 완료되지 않았습니다.")
        print("   위의 지침에 따라 수동으로 설정하세요.") 