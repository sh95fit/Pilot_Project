#!/bin/sh
set -e

# 환경변수 검증
if [ -z "$REDIS_USERNAME" ] || [ -z "$REDIS_PASSWORD" ]; then
    echo "Error: REDIS_USERNAME and REDIS_PASSWORD must be set"
    exit 1
fi

# Redis 설정 디렉토리 생성
mkdir -p /usr/local/etc/redis

# Redis 설정 파일을 직접 생성
cat > /usr/local/etc/redis/redis.conf << EOF
# 기본 설정
bind 0.0.0.0
protected-mode yes
port 6379
dir /data

# 데이터 영속화
appendonly yes

# 기본 계정 비활성화
user default off

# 신규 계정
# user $REDIS_USERNAME on >$REDIS_PASSWORD ~* &* +@all
user $REDIS_USERNAME on >$REDIS_PASSWORD ~* +@all
EOF

# 설정 파일 권한 설정 (보안 강화)
chmod 600 /usr/local/etc/redis/redis.conf

echo "Redis configuration created successfully for user: $REDIS_USERNAME"
echo "Configuration file permissions: $(ls -la /usr/local/etc/redis/redis.conf)"

# Redis 서버 시작
exec redis-server /usr/local/etc/redis/redis.conf