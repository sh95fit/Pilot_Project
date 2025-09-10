# scripts/setup.sh
#!/bin/bash

set -e

echo "🚀 Business Dashboard 개발 환경 설정 시작..."

# Poetry 설치 확인
if ! command -v poetry &> /dev/null; then
    echo "📦 Poetry가 설치되어 있지 않습니다. 설치 중..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# 가상환경 설정
echo "🐍 Python 가상환경 설정 중..."
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# 의존성 설치
echo "📚 의존성 설치 중..."
poetry install

# requirements.txt 생성 (Docker용)
echo "📄 requirements.txt 생성 중..."
poetry export -f requirements.txt --output services/business/backend/requirements.txt --without-hashes
poetry export -f requirements.txt --output services/business/frontend/requirements.txt --without-hashes

# 환경 파일 설정
echo "⚙️  환경 파일 설정 중..."
if [ ! -f config/dev.env ]; then
    cp config/.env.example config/dev.env
    echo "✅ config/dev.env 파일을 생성했습니다."
    echo "🔧 환경 변수를 설정해주세요:"
    echo "   - AWS Cognito 설정"
    echo "   - MySQL 연결 정보"
    echo "   - Supabase 설정"
    echo "   - SSH 키 경로"
fi

# SSH 키 디렉토리 생성
mkdir -p keys
echo "🔑 SSH 키 디렉토리를 생성했습니다: ./keys"

# 로그 디렉토리 생성
mkdir -p logs
echo "📝 로그 디렉토리를 생성했습니다: ./logs"

# Docker 네트워크 생성
echo "🐳 Docker 네트워크 설정 중..."
docker network create business_network 2>/dev/null || echo "네트워크가 이미 존재합니다."

echo "✅ 개발 환경 설정이 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
echo "1. config/dev.env 파일의 환경 변수를 설정하세요"
echo "2. SSH 키 파일을 keys/ 디렉토리에 복사하세요"
echo "3. 'docker-compose up --build' 명령으로 서비스를 시작하세요"
echo ""
echo "🔗 접속 URL:"
echo "   - Frontend: http://localhost:8501"
echo "   - Backend API: http://localhost:8000"
echo "   - API 문서: http://localhost:8000/docs"