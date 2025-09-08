# services/business/frontend/Dockerfile
FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry
WORKDIR /app

COPY pyproject.toml poetry.lock* ./

FROM base AS dev
RUN poetry config virtualenvs.create false && \
    poetry install --no-root
COPY services/business/frontend/. ./
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

FROM base AS prod
RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root
COPY services/business/frontend/. ./

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true"]