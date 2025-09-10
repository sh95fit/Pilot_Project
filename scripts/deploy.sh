# scripts/deploy.sh
#!/bin/bash

set -e

ENVIRONMENT=${1:-prod}
REMOTE_HOST=${2:-"your-server.com"}
REMOTE_USER=${3:-"ubuntu"}

echo "🚀 Business Dashboard 배포 시작 - 환경: $ENVIRONMENT"

# 배포 전 검증
echo "🔍 배포 전 검증 중..."

# 환경 파일 확인
if [ ! -f "config/${ENVIRONMENT}.env" ]; then
    echo "❌ config/${ENVIRONMENT}.env 파일이 존재하지 않습니다."
    exit 1
fi

# Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드 중..."
docker-compose -f services/business/compose/docker-compose.yml build

# 이미지 태그 지정
IMAGE_TAG=$(date +%Y%m%d_%H%M%S)
docker tag business_backend:latest business_backend:$IMAGE_TAG
docker tag business_frontend:latest business_frontend:$IMAGE_TAG

echo "✅ 이미지 빌드 완료: $IMAGE_TAG"

if [ "$ENVIRONMENT" = "prod" ]; then
    # 프로덕션 배포
    echo "🌐 프로덕션 서버에 배포 중..."
    
    # 서버에 파일 전송
    scp -r services/business/compose/ $REMOTE_USER@$REMOTE_HOST:~/business/
    scp config/${ENVIRONMENT}.env $REMOTE_USER@$REMOTE_HOST:~/business/config/
    
    # 원격 서버에서 배포 실행
    ssh $REMOTE_USER@$REMOTE_HOST << EOF
        cd ~/business
        
        # 기존 서비스 중지
        docker-compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml down
        
        # 새 이미지로 서비스 시작
        ENVIRONMENT=$ENVIRONMENT BUILD_TARGET=prod docker-compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d
        
        # 헬스 체크
        sleep 30
        curl -f http://localhost:8000/health || exit 1
        
        echo "✅ 프로덕션 배포 완료!"
EOF

else
    # 개발/스테이징 배포
    echo "🧪 개발 환경 배포 중..."
    
    # 기존 컨테이너 중지
    docker-compose -f services/business/compose/docker-compose.yml down
    
    # 새 컨테이너 시작
    ENVIRONMENT=$ENVIRONMENT docker-compose -f services/business/compose/docker-compose.yml up -d
    
    # 헬스 체크
    echo "🏥 헬스 체크 중..."
    sleep 15
    
    max_attempts=10
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health; then
            echo "✅ 헬스 체크 성공!"
            break
        else
            echo "⏳ 헬스 체크 실패 ($attempt/$max_attempts), 5초 후 재시도..."
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ 헬스 체크 실패. 배포를 롤백합니다."
        docker-compose -f services/business/compose/docker-compose.yml logs
        exit 1
    fi
fi

echo "🎉 배포가 성공적으로 완료되었습니다!"
echo "🔗 접속 정보:"
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "   - Frontend: http://$REMOTE_HOST:8501"
    echo "   - Backend: http://$REMOTE_HOST:8000"
else
    echo "   - Frontend: http://localhost:8501"
    echo "   - Backend: http://localhost:8000"
fi