#!/bin/bash
# nginx 설정 자동 적용 스크립트
# 사용법: ./apply_nginx_config.sh <user_id> <config_file_path>

set -e

USER_ID="$1"
CONFIG_FILE="$2"

if [ -z "$USER_ID" ] || [ -z "$CONFIG_FILE" ]; then
    echo "사용법: $0 <user_id> <config_file_path>"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 설정 파일을 찾을 수 없습니다: $CONFIG_FILE"
    exit 1
fi

echo "🔧 nginx 설정 적용 시작: 사용자 $USER_ID"

# 1. sites-available에 복사
sudo cp "$CONFIG_FILE" "/etc/nginx/sites-available/${USER_ID}.conf"
echo "✅ 설정 파일 복사 완료: /etc/nginx/sites-available/${USER_ID}.conf"

# 2. sites-enabled에 심볼릭 링크 생성 (기존 것 제거 후)
sudo rm -f "/etc/nginx/sites-enabled/${USER_ID}.conf"
sudo ln -s "/etc/nginx/sites-available/${USER_ID}.conf" "/etc/nginx/sites-enabled/${USER_ID}.conf"
echo "✅ 심볼릭 링크 생성 완료: /etc/nginx/sites-enabled/${USER_ID}.conf"

# 3. nginx 설정 테스트
if sudo nginx -t; then
    echo "✅ nginx 설정 테스트 통과"
    
    # 4. nginx 리로드
    if sudo systemctl reload nginx; then
        echo "✅ nginx 리로드 완료"
        echo "🌐 사용자 $USER_ID 웹사이트 활성화: http://localhost/$USER_ID"
    else
        echo "❌ nginx 리로드 실패"
        exit 1
    fi
else
    echo "❌ nginx 설정 테스트 실패"
    # 실패 시 심볼릭 링크 제거
    sudo rm -f "/etc/nginx/sites-enabled/${USER_ID}.conf"
    exit 1
fi

echo "🎉 nginx 설정 적용 완료" 