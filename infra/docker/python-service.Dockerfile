# syntax=docker/dockerfile:1.7
# One recipe for every Python service in the uv workspace (mini_ums_api, orchestrator, gateway).
# Build context: the repo root. PACKAGE picks the workspace member, MODULE its import name.
FROM python:3.11.18-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv

ARG PACKAGE
ARG MODULE
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    APP_MODULE=${MODULE}

WORKDIR /src

# Third-party dependencies first, so source edits don't reinstall them.
COPY pyproject.toml uv.lock ./
COPY libs/common/pyproject.toml libs/common/
COPY apps/mini_ums_api/pyproject.toml apps/mini_ums_api/
COPY apps/orchestrator/pyproject.toml apps/orchestrator/
COPY apps/gateway/pyproject.toml apps/gateway/
COPY rag/pyproject.toml rag/
COPY language/pyproject.toml language/
COPY sentiment/pyproject.toml sentiment/
COPY eval/pyproject.toml eval/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace --package "$PACKAGE"

COPY libs libs
COPY apps apps
COPY rag rag
COPY language language
COPY sentiment sentiment
COPY eval eval
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package "$PACKAGE"

RUN useradd --system --uid 10001 app
USER app
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn \"${APP_MODULE}.main:create_app\" --factory --host 0.0.0.0 --port 8000"]
