# syntax=docker/dockerfile:1.7

# ---- builder ---------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# uv is shipped as a static binary in a distroless image — copy it in.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Layer 1: dependencies only. Cached unless pyproject.toml or uv.lock change.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Layer 2: install the project itself.
COPY storage_service ./storage_service
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ---- runtime ---------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Non-root user — limits blast radius if the container is compromised.
RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --home-dir /app --shell /sbin/nologin app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/storage_service /app/storage_service

# Persistence dir for the on-disk snapshot. In compose/k8s this is shadowed
# by a volume mount; when running the image standalone we still need it to
# exist and be writable by uid 1001.
RUN install -d -o app -g app /app/mnt

# venv on PATH → the `start` console script is callable directly.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/probes/liveness',timeout=3).status==200 else 1)"

CMD ["start"]
