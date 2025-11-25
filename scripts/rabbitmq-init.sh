#!/bin/sh
set -e

# .env 파일 로드
if [ -f /app/config/dev.env ]; then
    export $(grep -v '^#' /app/config/dev.env | xargs)
fi

# 환경 변수 검증
if [ -z "$RABBITMQ_USER" ] || [ -z "$RABBITMQ_PASS" ]; then
    echo "Error: RABBITMQ_USER and RABBITMQ_PASS must be set"
    exit 1
fi

# RabbitMQ 서버를 백그라운드로 시작
rabbitmq-server -detached

# 서버가 완전히 시작될 때까지 대기
echo "Waiting for RabbitMQ to start..."
until rabbitmqctl status > /dev/null 2>&1; do
    sleep 1
done

# 사용자 계정 생성
rabbitmqctl list_users | grep -q "^$RABBITMQ_USER$" || \
rabbitmqctl add_user "$RABBITMQ_USER" "$RABBITMQ_PASS"
rabbitmqctl set_user_tags "$RABBITMQ_USER" administrator
rabbitmqctl set_permissions -p / "$RABBITMQ_USER" ".*" ".*" ".*"

echo "RabbitMQ initialization completed"

# detached 프로세스를 중지하고 포그라운드로 재시작
rabbitmqctl stop_app
rabbitmqctl stop

# 포그라운드로 서버 시작
exec rabbitmq-server