# services/business/frontend/Dockerfile
FROM python:3.11-slim

ARG ENVIRONMENT=dev
ENV ENVIRONMENT=${ENVIRONMENT}

RUN pip install --no-cache-dir poetry

WORKDIR /app

# pyproject.toml과 poetry.lock을 빌드 컨텍스트 기준으로 복사
COPY pyproject.toml poetry.lock* services/business/frontend/

# 의존성 설치
RUN poetry config virtualenvs.create false && \
    if [ "$ENVIRONMENT" = "prod" ]; then \
        poetry install --no-dev --no-root; \
    else \
        poetry install --no-root; \
    fi

# 프론트엔드 소스코드 복사
COPY services/business/frontend/ ./

EXPOSE 8501

CMD streamlit run app.py --server.port 8501 --server.address 0.0.0.0
