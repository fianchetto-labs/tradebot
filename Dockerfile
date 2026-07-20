# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14
FROM python:${PYTHON_VERSION}-slim

ENV PIP_NO_CACHE_DIR=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TRADEBOT_HEALTHCHECK_PORT=8080

WORKDIR /app

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/usr/sbin/nologin" \
    --no-create-home \
    --uid 10001 \
    tradebot

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY deploy ./deploy

RUN python -m pip install --upgrade pip \
    && python -m pip install -e .

USER tradebot

EXPOSE 8080 8081 8082 8090

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import os, urllib.request; port = os.environ.get('TRADEBOT_HEALTHCHECK_PORT', '8080'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health-check', timeout=2).read()"

CMD ["python", "-m", "fianchetto_tradebot.server.orders.serving.orders_rest_service"]
