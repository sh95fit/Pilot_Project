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

# 시스템 의존성 설치 + tzdata 설치 (한국 시간대 적용)
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 한국국 시간대 적용
ENV TZ=Asia/Seoul

# Poetry 설치
RUN pip install --no-cache-dir poetry

WORKDIR /app
ENV PYTHONPATH=/app

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
COPY ./services/business/backend/. ./backend

# 빌드 타임에 권할 설정을 처리하므로 런타임에 실행되는 볼륨 마운트보다 빨라 config 권한 처리가 되지 않음
# 운영 서버는 우분투 서버로 계정이 ubuntu에 맞춰 권한 세팅 (ubuntu uid = 1001) -> 워크플로우에서 동적으로 받아 도커컴포즈에서 user로 할당하도록 변경
# 비특권 사용자 생성 및 권한 설정
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =========================
# 프로덕션 단계
# =========================
FROM base AS prod

# ARG 선언만 추가하면 docker-compose의 args가 전달됨
ARG APP_UID=1001
ARG APP_GID=1001

RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# 소스 코드 복사
COPY ./shared/. ./shared
COPY ./services/business/backend/. ./backend

# 운영 서버는 우분투 서버로 계정이 ubuntu에 맞춰 권한 세팅 (ubuntu uid = 1001) -> 워크플로우에서 동적으로 받아 도커컴포즈에서 user로 할당하도록 변경
# RUN adduser --disabled-password --gecos '' appuser && \
#     chown -R appuser:appuser /app

# USER appuser

# 동적 UID/GID 사용
RUN groupadd -g ${APP_GID} appuser && \
    useradd -u ${APP_UID} -g ${APP_GID} -m -s /bin/bash appuser && \
    chown -R ${APP_UID}:${APP_GID} /app

USER ${APP_UID}:${APP_GID}


EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]