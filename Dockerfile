# syntax=docker/dockerfile:1.7

FROM python:3.14-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY storage_service ./storage_service
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.14-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="storage-service" \
      org.opencontainers.image.description="In-memory JSON object storage with TTL, persisted across restarts." \
      org.opencontainers.image.source="https://github.com/MaxBarannikov/kubernetes-fastAPI-project"

RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --home-dir /app --shell /sbin/nologin app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/storage_service /app/storage_service

# In compose/k8s this is shadowed by a volume; standalone needs it writable by uid 1001.
RUN install -d -o app -g app /app/mnt

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000

# The shutdown snapshot hangs off SIGTERM.
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/probes/liveness',timeout=3).status==200 else 1)"

CMD ["start"]
