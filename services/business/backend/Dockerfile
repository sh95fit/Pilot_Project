# services/business/backend/Dockerfile
FROM python:3.11-slim AS base

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install --no-cache-dir poetry

WORKDIR /app

# Poetry 의존성 파일 복사
COPY pyproject.toml poetry.lock* ./

# =========================
# 개발 단계
# =========================
FROM base AS dev

RUN poetry config virtualenvs.create false && \
    poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# 소스 코드 복사
COPY ./shared/. ./shared
COPY ./services/business/backend/. ./

# 비특권 사용자 생성 및 권한 설정
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =========================
# 프로덕션 단계
# =========================
FROM base AS prod

RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# 소스 코드 복사
COPY ./shared/. ./shared
COPY ./services/business/backend/. ./


RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]