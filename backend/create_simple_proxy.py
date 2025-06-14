#!/usr/bin/env python3
"""
간단한 nginx 프록시 설정 생성 스크립트
과제 요구사항: /<user_id> -> VM 웹포트 프록시
"""

import os
import subprocess
from pathlib import Path

def create_simple_proxy():
    """간단한 nginx 프록시 설정 생성"""
    
    # 기본 nginx 프록시 설정
    proxy_config = """# 웹 호스팅 서비스 프록시 설정
server {
    listen 80 default_server;
    server_name _;
    
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
                .user-list {
                    text-align: left;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 웹 호스팅 서비스</h1>
                <p>사용자별 접속 방법:</p>
                <div class="user-list">
                    <p>• /7 - 사용자 ID 7의 웹호스팅</p>
                    <p>• /8 - 사용자 ID 8의 웹호스팅</p>
                    <p>• 직접 접속: :8XXX 포트</p>
                </div>
            </div>
        </body>
        </html>';
        add_header Content-Type text/html;
    }
    
    # 사용자 7번 프록시 (예시)
    location /7 {
        rewrite ^/7(/.*)$ $1 break;
        rewrite ^/7$ / break;
        proxy_pass http://127.0.0.1:8007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # 사용자 8번 프록시 (예시)  
    location /8 {
        rewrite ^/8(/.*)$ $1 break;
        rewrite ^/8$ / break;
        proxy_pass http://127.0.0.1:8008;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # 동적 사용자 프록시 (범위: 1-50)
    location ~ ^/([1-9]|[1-4][0-9]|50)$ {
        set $user_id $1;
        rewrite ^/([1-9]|[1-4][0-9]|50)$ / break;
        proxy_pass http://127.0.0.1:80$user_id;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location ~ ^/([1-9]|[1-4][0-9]|50)/ {
        set $user_id $1;
        rewrite ^/([1-9]|[1-4][0-9]|50)/(.*) /$2 break;
        proxy_pass http://127.0.0.1:80$user_id;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
"""
    
    try:
        # nginx 설정 디렉토리 생성
        config_dir = Path("nginx-configs")
        config_dir.mkdir(exist_ok=True)
        
        # 설정 파일 저장
        config_file = config_dir / "proxy.conf"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(proxy_config)
        
        print(f"✅ 프록시 설정 파일 생성: {config_file}")
        
        # Docker nginx 컨테이너로 프록시 실행
        print("\n🐳 Docker nginx 프록시 컨테이너 시작...")
        
        # 기존 프록시 컨테이너 정리
        subprocess.run(["docker", "rm", "-f", "webhost-proxy"], 
                      capture_output=True)
        
        # nginx 프록시 컨테이너 실행
        docker_cmd = [
            "docker", "run", "-d",
            "--name", "webhost-proxy",
            "-p", "80:80",  # 호스트 80포트를 컨테이너 80포트로
            "-v", f"{config_file.absolute()}:/etc/nginx/conf.d/default.conf",
            "--network", "host",  # 호스트 네트워크 사용으로 다른 컨테이너 접근
            "nginx:alpine"
        ]
        
        result = subprocess.run(docker_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ nginx 프록시 컨테이너 시작 완료")
            print(f"🌐 접속 URL: http://192.168.122.115/")
            print(f"📋 사용자별 접속: http://192.168.122.115/7 (사용자 ID 7)")
            return True
        else:
            print(f"❌ nginx 프록시 컨테이너 시작 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 프록시 설정 실패: {e}")
        return False

def check_containers():
    """실행 중인 컨테이너 확인"""
    try:
        result = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\\t{{.Ports}}"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("📦 실행 중인 컨테이너:")
            print(result.stdout)
        return True
    except Exception as e:
        print(f"❌ 컨테이너 확인 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 간단한 nginx 프록시 설정 시작...")
    
    # 1. 프록시 설정 생성 및 실행
    proxy_ok = create_simple_proxy()
    
    if proxy_ok:
        print("\n📦 컨테이너 상태 확인:")
        check_containers()
        
        print("\n" + "="*60)
        print("🎉 nginx 프록시 설정 완료!")
        print("🌐 메인 페이지: http://192.168.122.115/")
        print("👤 사용자별 접속: http://192.168.122.115/<user_id>")
        print("📝 예시: http://192.168.122.115/7")
        print("="*60)
    else:
        print("\n❌ 프록시 설정에 실패했습니다.")
        print("   수동으로 nginx를 설정하거나 직접 포트로 접속하세요.") 