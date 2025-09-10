#!/bin/bash

set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "💾 Business Dashboard 백업 시작..."

# 환경 설정 백업
echo "⚙️ 환경 설정 백업 중..."
cp -r config/ $BACKUP_DIR/

# Supabase 데이터 백업 (pg_dump 사용)
echo "🟢 Supabase 데이터 백업 중..."
if command -v pg_dump &> /dev/null; then
    pg_dump $DATABASE_URL > $BACKUP_DIR/supabase_backup.sql
    echo "✅ Supabase 백업 완료"
else
    echo "⚠️ pg_dump가 설치되어 있지 않습니다. Supabase 백업을 건너뜁니다."
fi

# MySQL 데이터 백업은 SSH 터널을 통해 실행해야 하므로 별도 스크립트 필요
echo "🐬 MySQL 백업은 운영팀에서 별도로 관리합니다."

# 애플리케이션 코드 백업
echo "📦 애플리케이션 코드 백업 중..."
tar -czf $BACKUP_DIR/app_code.tar.gz \
    services/ \
    shared/ \
    pyproject.toml \
    poetry.lock \
    scripts/

# Docker 이미지 백업
echo "🐳 Docker 이미지 백업 중..."
docker save business_backend:latest | gzip > $BACKUP_DIR/backend_image.tar.gz
docker save business_frontend:latest | gzip > $BACKUP_DIR/frontend_image.tar.gz

echo "✅ 백업이 완료되었습니다: $BACKUP_DIR"
echo "📊 백업 크기:"
du -sh $BACKUP_DIR

# 오래된 백업 파일 정리 (7일 이상)
echo "🧹 오래된 백업 파일 정리 중..."
find ./backups/ -name "*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true

echo "🎉 백업 작업이 완료되었습니다!"


# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE_NAME: business-backend
  FRONTEND_IMAGE_NAME: business-frontend

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - name: 체크아웃
      uses: actions/checkout@v4
    
    - name: Python 설정
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Poetry 설치
      uses: snok/install-poetry@v1
      with:
        version: 1.6.1
        virtualenvs-create: true
        virtualenvs-in-project: true
    
    - name: 의존성 설치
      run: poetry install
    
    - name: 코드 품질 검사
      run: |
        poetry run black --check .
        poetry run isort --check-only .
        poetry run flake8 . --max-line-length=88 --extend-ignore=E203,W503
    
    - name: 타입 검사
      run: poetry run mypy services/business/backend/app --ignore-missing-imports
    
    - name: 테스트 실행
      run: |
        cd services/business/backend
        poetry run pytest tests/ -v --cov=app

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - name: 체크아웃
      uses: actions/checkout@v4
    
    - name: Container Registry 로그인
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: 메타데이터 추출
      id: meta-backend
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ github.repository_owner }}/${{ env.BACKEND_IMAGE_NAME }}
        tags