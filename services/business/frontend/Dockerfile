# services/business/frontend/Dockerfile
# services/business/frontend/Dockerfile
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# 시스템 의존성 설치 + tzdata 설치 (한국 시간대 적용)
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 한국 시간대 적용
ENV TZ=Asia/Seoul

# Poetry 설치
RUN pip install --no-cache-dir poetry

WORKDIR /app
ENV PYTHONPATH=/app/frontend

# Poetry 의존성 파일 복사
COPY pyproject.toml poetry.lock* ./

# 소스 코드 복사
COPY ./shared/. ./shared
COPY ./services/business/frontend/. ./frontend

# =========================
# 개발 단계
# =========================
FROM base AS dev

RUN poetry config virtualenvs.create false && \
    poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# 비특권 사용자 생성 및 권한 설정
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8501
CMD ["poetry", "run", "streamlit", "run", "frontend/app/main.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

# =========================
# 프로덕션 단계 - 완전한 권한 이슈 해결
# =========================
FROM base AS prod

RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# 동적 UID/GID 지원
ARG USER_UID=1000
ARG USER_GID=1000

# 사용자 생성 및 필요한 디렉토리 미리 생성 (권한 이슈 해결)
RUN addgroup --gid $USER_GID appuser && \
    adduser --disabled-password --gecos '' --uid $USER_UID --gid $USER_GID appuser && \
    mkdir -p /home/appuser/.streamlit && \
    mkdir -p /home/appuser/.config && \
    mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /app /home/appuser

COPY services/business/frontend/.streamlit/config.toml /home/appuser/.streamlit/config.toml
RUN chown appuser:appuser /home/appuser/.streamlit/config.toml

# # 환경 변수 설정 (완전한 권한 이슈 방지)
ENV HOME=/home/appuser \
    USER=appuser \
    STREAMLIT_CONFIG_DIR=/home/appuser/.streamlit \
    XDG_CONFIG_HOME=/home/appuser/.config \
    XDG_CACHE_HOME=/home/appuser/.cache \
    XDG_DATA_HOME=/home/appuser/.local/share \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

USER appuser

EXPOSE 8501
CMD ["poetry", "run", "streamlit", "run", "frontend/app/main.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]