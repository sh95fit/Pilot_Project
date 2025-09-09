#!/bin/bash

# Poetry 설치 확인
if ! command -v poetry &> /dev/null; then
    echo "Poetry가 설치되어 있지 않습니다. 설치 중..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# 의존성 설치
echo "의존성 설치 중..."
poetry install

# requirements.txt 생성 (Docker용)
echo "requirements.txt 생성 중..."
poetry export -f requirements.txt --output services/business/backend/requirements.txt --without-hashes
poetry export -f requirements.txt --output services/business/frontend/requirements.txt --without-hashes

# 환경 파일 복사
if [ ! -f config/dev.env ]; then
    cp config/.env.example config/dev.env
    echo "config/dev.env 파일을 생성했습니다. 환경 변수를 설정해주세요."
fi

echo "설정 완료!"