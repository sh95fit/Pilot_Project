#!/bin/bash
# scripts/deploy.sh

ENVIRONMENT=${1:-dev}
SERVICE_PATH="services/business/compose"

cd $SERVICE_PATH

case $ENVIRONMENT in
  "dev")
    echo "🚀 Starting development environment..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    ;;
  "prod")
    echo "🚀 Starting production environment..."
    BUILD_TARGET=prod ENVIRONMENT=prod docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    ;;
  *)
    echo "❌ Invalid environment. Use 'dev' or 'prod'"
    exit 1
    ;;
esac

echo "⏳ Waiting for services to start..."
sleep 10