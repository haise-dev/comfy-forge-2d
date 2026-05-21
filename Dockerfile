FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN uv pip install --system fastapi uvicorn pydantic celery redis websocket-client

COPY api /app/api
COPY scripts /app/scripts
COPY comfy_workflows /app/comfy_workflows
