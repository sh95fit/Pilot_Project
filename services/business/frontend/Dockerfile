# services/business/frontend/Dockerfile
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

COPY ./services/business/frontend ./

EXPOSE 8501

CMD streamlit run app.py --server.port 8501 --server.address 0.0.0.0
