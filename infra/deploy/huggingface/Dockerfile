# syntax=docker/dockerfile:1.7
# All-in-one image for the free Hugging Face Space demo (D-038). Build context: the repo root.
# Postgres + pgvector, Redis, the three Python services, the Next.js portal and the widget run
# in one container under supervisord. Caddy serves everything on the Space's one port (7860);
# every other service listens on 127.0.0.1 only.

FROM node:24.22.2-bookworm-slim AS web
WORKDIR /web
COPY apps/mini_ums_web/package.json apps/mini_ums_web/package-lock.json ./
RUN npm ci
COPY apps/mini_ums_web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:24.22.2-bookworm-slim AS widget
WORKDIR /widget
COPY apps/widget/package.json apps/widget/package-lock.json ./
RUN npm ci
COPY apps/widget/ ./
RUN npm run build

FROM pgvector/pgvector:0.8.7-pg16
RUN apt-get update \
    && apt-get install -y --no-install-recommends redis-server supervisor ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=caddy:2.10.2 /usr/bin/caddy /usr/local/bin/caddy
COPY --from=node:24.22.2-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON=3.11 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:/usr/lib/postgresql/16/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY libs libs
COPY apps/mini_ums_api apps/mini_ums_api
COPY apps/orchestrator apps/orchestrator
COPY apps/gateway apps/gateway
COPY rag rag
COPY language language
COPY sentiment sentiment
COPY eval eval
RUN uv python install 3.11 && uv sync --frozen --no-dev --no-editable --all-packages

COPY --from=web /web/.next/standalone /app/web
COPY --from=web /web/.next/static /app/web/.next/static
COPY --from=widget /widget/dist/widget.js /app/widget/widget.js
COPY infra/deploy/huggingface/Caddyfile infra/deploy/huggingface/supervisord.conf \
     infra/deploy/huggingface/entrypoint.sh /app/deploy/
RUN chmod 755 /app/deploy/entrypoint.sh && useradd --create-home --uid 1000 user

# Non-secret wiring; secrets (provider keys) come from the Space's settings at run time.
ENV ENVIRONMENT=prod \
    DEMO_ACCOUNTS=true \
    SESSION_COOKIE_SECURE=true \
    DATABASE_URL=postgresql://voiceserve@127.0.0.1:5432/voiceserve \
    REDIS_URL=redis://127.0.0.1:6379/0 \
    MINI_UMS_API_URL=http://127.0.0.1:8001 \
    ORCHESTRATOR_URL=http://127.0.0.1:8002 \
    GATEWAY_URL=http://127.0.0.1:8003 \
    WIDGET_URL=/widget.js \
    SEED_STUDENTS=300

# Spaces run the container as uid 1000.
USER user
ENV HOME=/home/user
EXPOSE 7860
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
CMD []
