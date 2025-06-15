#!/bin/bash
# nginx 설정 제거 스크립트
# 사용법: ./remove_nginx_config.sh <user_id>

set -e

USER_ID="$1"

if [ -z "$USER_ID" ]; then
    echo "사용법: $0 <user_id>"
    exit 1
fi

echo "🗑️ nginx 설정 제거 시작: 사용자 $USER_ID"

# 1. sites-enabled에서 심볼릭 링크 제거
if [ -L "/etc/nginx/sites-enabled/${USER_ID}.conf" ]; then
    sudo rm "/etc/nginx/sites-enabled/${USER_ID}.conf"
    echo "✅ 심볼릭 링크 제거 완료: /etc/nginx/sites-enabled/${USER_ID}.conf"
fi

# 2. sites-available에서 설정 파일 제거
if [ -f "/etc/nginx/sites-available/${USER_ID}.conf" ]; then
    sudo rm "/etc/nginx/sites-available/${USER_ID}.conf"
    echo "✅ 설정 파일 제거 완료: /etc/nginx/sites-available/${USER_ID}.conf"
fi

# 3. nginx 설정 테스트 및 리로드
if sudo nginx -t; then
    echo "✅ nginx 설정 테스트 통과"
    
    if sudo systemctl reload nginx; then
        echo "✅ nginx 리로드 완료"
        echo "🌐 사용자 $USER_ID 웹사이트 비활성화 완료"
    else
        echo "❌ nginx 리로드 실패"
        exit 1
    fi
else
    echo "❌ nginx 설정 테스트 실패"
    exit 1
fi

echo "🎉 nginx 설정 제거 완료" 