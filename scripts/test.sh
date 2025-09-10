#!/bin/bash

set -e

echo "🧪 Business Dashboard 테스트 시작..."

# Poetry 환경에서 테스트 실행
echo "📊 Backend 테스트 실행 중..."
cd services/business/backend
poetry run pytest tests/ -v --cov=app --cov-report=html

echo "🎨 Frontend 테스트 (Streamlit 검증) 실행 중..."
cd ../frontend
poetry run python -c "
import streamlit
import sys
sys.path.append('.')
print('✅ Streamlit 모듈 import 성공')

# 기본 앱 구문 검사
import app.main
print('✅ 메인 앱 모듈 검증 성공')

import app.pages.1_📊_Dashboard as dashboard
import app.pages.2_👥_Customers as customers  
import app.pages.3_⚙️_Settings as settings
print('✅ 모든 페이지 모듈 검증 성공')
"

echo "🔍 코드 품질 검사 실행 중..."
cd ../../..

# Black 포맷터 검사
echo "🖤 Black 포맷터 검사..."
poetry run black --check services/business/backend/app services/business/frontend/app shared/

# isort import 정렬 검사  
echo "📚 Import 정렬 검사..."
poetry run isort --check-only services/business/backend/app services/business/frontend/app shared/

# Flake8 린터
echo "🔍 Flake8 린터 검사..."
poetry run flake8 services/business/backend/app services/business/frontend/app shared/ --max-line-length=88 --extend-ignore=E203,W503

echo "🐳 Docker 빌드 테스트..."
docker-compose -f services/business/compose/docker-compose.yml build

echo "✅ 모든 테스트가 성공적으로 완료되었습니다!"
