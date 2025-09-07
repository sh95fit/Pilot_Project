# services/business/backend/Dockerfile
FROM python:3.11-slim

ARG ENVIRONMENT=dev
ENV ENVIRONMENT=${ENVIRONMENT}

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && \
    if [ "$ENVIRONMENT" = "prod" ]; then \
        poetry install --no-dev --no-root; \
    else \
        poetry install --no-root; \
    fi

COPY ./services/business/backend ./

EXPOSE 8000

CMD if [ "$ENVIRONMENT" = "prod" ]; then \
        uvicorn main:app --host 0.0.0.0 --port 8000; \
    else \
        uvicorn main:app --reload --host 0.0.0.0 --port 8000; \
    fi
