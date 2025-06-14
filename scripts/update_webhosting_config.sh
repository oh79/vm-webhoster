#!/bin/bash
# webhosting.conf 자동 업데이트 스크립트 (개선된 버전)
# 사용법: ./update_webhosting_config.sh <user_id> <web_port>

set -e

USER_ID="$1"
WEB_PORT="$2"

if [ -z "$USER_ID" ] || [ -z "$WEB_PORT" ]; then
    echo "사용법: $0 <user_id> <web_port>"
    exit 1
fi

WEBHOSTING_CONFIG="/etc/nginx/sites-available/webhosting"
BACKUP_CONFIG="/etc/nginx/sites-available/webhosting.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 webhosting.conf 자동 업데이트 시작: 사용자 $USER_ID (포트 $WEB_PORT)"

# 1. 기존 설정 백업
sudo cp "$WEBHOSTING_CONFIG" "$BACKUP_CONFIG"
echo "✅ 기존 설정 백업: $BACKUP_CONFIG"

# 2. 사용자 location 블록이 이미 있는지 확인
if sudo grep -q "location /$USER_ID" "$WEBHOSTING_CONFIG"; then
    echo "⚠️ 사용자 $USER_ID의 설정이 이미 존재합니다. 포트만 업데이트합니다."
    # 해당 사용자의 포트만 업데이트
    sudo sed -i "/location \/$USER_ID/,/}/ s|proxy_pass http://127.0.0.1:[0-9]*;|proxy_pass http://127.0.0.1:$WEB_PORT;|g" "$WEBHOSTING_CONFIG"
else
    echo "📝 새로운 사용자 $USER_ID 설정 추가 중..."
    
    # 3. 새로운 location 블록을 임시 파일로 생성
    cat > /tmp/new_location_${USER_ID}.conf << EOF
    
    # 사용자 ${USER_ID}번 VM 호스팅 (포트 ${WEB_PORT})
    location /${USER_ID} {
        rewrite ^/${USER_ID}(/.*)$ \$1 break;
        rewrite ^/${USER_ID}$ / break;
        
        proxy_pass http://127.0.0.1:${WEB_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
EOF
    
    # 4. server 블록의 마지막 } 바로 앞에 새로운 location 블록 추가
    # 더 안전한 방법: 마지막 줄(})을 제거하고 새로운 내용 추가 후 }를 다시 추가
    sudo sh -c "head -n -1 '$WEBHOSTING_CONFIG' > /tmp/webhosting_temp && 
                cat /tmp/new_location_${USER_ID}.conf >> /tmp/webhosting_temp && 
                echo '}' >> /tmp/webhosting_temp && 
                mv /tmp/webhosting_temp '$WEBHOSTING_CONFIG'"
    
    # 5. 메인 페이지의 사용자 목록 업데이트
    sudo sed -i "s|활성 사용자: [^<]*|활성 사용자: 9, 10, 11, 12, $USER_ID|" "$WEBHOSTING_CONFIG"
    
    # 임시 파일 삭제
    rm -f /tmp/new_location_${USER_ID}.conf
fi

echo "✅ webhosting.conf 업데이트 완료"

# 6. nginx 설정 테스트
if sudo nginx -t; then
    echo "✅ nginx 설정 테스트 통과"
    
    # 7. nginx 리로드
    if sudo systemctl reload nginx; then
        echo "✅ nginx 리로드 완료"
        echo "🌐 사용자 $USER_ID 웹사이트 활성화: http://localhost/$USER_ID"
    else
        echo "❌ nginx 리로드 실패"
        # 실패 시 백업 복원
        sudo cp "$BACKUP_CONFIG" "$WEBHOSTING_CONFIG"
        exit 1
    fi
else
    echo "❌ nginx 설정 테스트 실패"
    # 실패 시 백업 복원
    sudo cp "$BACKUP_CONFIG" "$WEBHOSTING_CONFIG"
    exit 1
fi

echo "🎉 webhosting.conf 자동 업데이트 완료" 