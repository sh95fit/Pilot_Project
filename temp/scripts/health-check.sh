#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 설정
SERVICE_NAME="business"
BACKEND_PORTS=("8000" "8002")
FRONTEND_PORTS=("8501" "8503")

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 서비스 상태 확인
check_service_health() {
    local service_type=$1
    local port=$2
    local endpoint=$3
    
    if curl -f -s "http://localhost:${port}${endpoint}" > /dev/null; then
        log_info "$service_type on port $port: ✅ Healthy"
        return 0
    else
        log_error "$service_type on port $port: ❌ Unhealthy"
        return 1
    fi
}

# Docker 컨테이너 상태 확인
check_container_status() {
    log_info "=== Container Status ==="
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "$SERVICE_NAME"
    echo
}

# 서비스 헬스체크
check_services_health() {
    log_info "=== Service Health Check ==="
    
    local backend_healthy=0
    local frontend_healthy=0
    
    # 백엔드 서비스 확인
    for port in "${BACKEND_PORTS[@]}"; do
        if check_service_health "Backend API" "$port" "/health"; then
            backend_healthy=$((backend_healthy + 1))
        fi
    done
    
    # 프론트엔드 서비스 확인  
    for port in "${FRONTEND_PORTS[@]}"; do
        if check_service_health "Frontend App" "$port" "/_stcore/health"; then
            frontend_healthy=$((frontend_healthy + 1))
        fi
    done
    
    echo
    log_info "Backend services healthy: $backend_healthy/${#BACKEND_PORTS[@]}"
    log_info "Frontend services healthy: $frontend_healthy/${#FRONTEND_PORTS[@]}"
    
    if [ $backend_healthy -eq 0 ] || [ $frontend_healthy -eq 0 ]; then
        log_error "Critical: No healthy instances found!"
        return 1
    fi
    
    return 0
}

# Nginx 상태 확인
check_nginx_status() {
    log_info "=== Nginx Status ==="
    
    if docker exec business-nginx nginx -t 2>/dev/null; then
        log_info "Nginx configuration: ✅ Valid"
    else
        log_error "Nginx configuration: ❌ Invalid"
    fi
    
    if curl -f -s "http://localhost/health" > /dev/null; then
        log_info "Nginx proxy: ✅ Responding"
    else
        log_error "Nginx proxy: ❌ Not responding"
    fi
    echo
}

# 리소스 사용량 확인
check_resource_usage() {
    log_info "=== Resource Usage ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | grep -E "(CONTAINER|$SERVICE_NAME)"
    echo
}

# 메인 실행
main() {
    log_info "🏥 Starting health check for $SERVICE_NAME services..."
    echo
    
    check_container_status
    check_services_health
    check_nginx_status
    check_resource_usage
    
    if check_services_health >/dev/null 2>&1; then
        log_info "🎉 Overall system status: ✅ Healthy"
        exit 0
    else
        log_error "💀 Overall system status: ❌ Unhealthy"
        exit 1
    fi
}

main "$@"