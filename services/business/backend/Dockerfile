# services/business/backend/Dockerfile
FROM python:3.11-slim AS base

# 시스템 패키지 설치 및 업데이트
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry
WORKDIR /app

# Poetry 파일들을 루트에서 복사
COPY pyproject.toml poetry.lock* ./

# 개발 단계
FROM base AS dev
RUN poetry config virtualenvs.create false && \
    poetry install --no-root
COPY services/business/backend/. ./
EXPOSE 8000
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# 프로덕션 단계
FROM base AS prod
RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root
COPY services/business/backend/. ./

# 비특권 사용자 생성 및 권한 설정
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]