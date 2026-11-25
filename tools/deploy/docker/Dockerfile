# syntax=docker/dockerfile:1.7
# =============================================================================
# Production Python Container
# =============================================================================
ARG PYTHON_VERSION=3.13
ARG DEBIAN_VERSION=bookworm
ARG BUILDER_IMAGE=python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION}
ARG UV_VERSION=0.13.8
ARG BUN_VERSION=1.4.5

FROM ${BUILDER_IMAGE} AS python-base

RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        tini \
        ca-certificates \
    && rm -rf /var/log/* /tmp/* \
    && mkdir -p /workspace/app

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/
COPY --from=oven/bun:1.4.5 /usr/local/bin/bun /usr/local/bin/bun

FROM python-base AS builder

ARG UV_INSTALL_ARGS="--no-dev"

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/workspace/app/.venv/bin:/usr/local/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DATABASE_POOL_DISABLED=true

RUN --mount=type=cache,id=apt-cache-builder,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib-builder,target=/var/lib/apt,sharing=locked \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/log/* /tmp/* \
    && mkdir -p /cloudsql

WORKDIR /workspace/app

COPY pyproject.toml uv.lock README.md ./
COPY src/js/web/package.json src/js/web/bun.lock ./src/js/web/
COPY src/js/web/biome.json src/js/web/vite.config.ts src/js/web/tsconfig.json src/js/web/openapi-ts.config.ts ./src/js/web/
COPY src/js/templates/package.json src/js/templates/bun.lock ./src/js/templates/

WORKDIR /workspace/app/src/js/web
RUN bun install --frozen-lockfile --ignore-scripts

WORKDIR /workspace/app/src/js/templates
RUN bun install --frozen-lockfile --ignore-scripts
WORKDIR /workspace/app

RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    uv venv \
    && uv sync ${UV_INSTALL_ARGS} --frozen --no-install-project --no-editable --no-build \
    && uv export ${UV_INSTALL_ARGS} --frozen --no-hashes --no-emit-project --output-file=requirements.txt

COPY tools ./tools/
COPY src/js/web/ ./src/js/web/
COPY src/js/templates/ ./src/js/templates/
COPY src/py/ ./src/py/

RUN mkdir -p src/py/app/server/static/web src/py/app/server/static/email

RUN cd src/js/templates && bun run build

RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    uv sync ${UV_INSTALL_ARGS} --frozen --no-editable --no-build \
    && app assets generate-types \
    && app assets build \
    && uv build --wheel --clear

FROM python-base AS runtime

ARG LITESTAR_APP="app.server.asgi:create_app"

ENV PATH="/workspace/app/.venv/bin:/usr/local/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LITESTAR_APP="${LITESTAR_APP}"

RUN groupadd --system --gid 65532 nonroot \
    && useradd --no-create-home --system --uid 65532 --gid 65532 nonroot \
    && mkdir -p /workspace/app \
    && chown -R nonroot:nonroot /workspace

COPY --from=builder --chown=65532:65532 /cloudsql /cloudsql
COPY --from=builder --chown=65532:65532 /workspace/app/requirements.txt /tmp/requirements.txt
COPY --from=builder --chown=65532:65532 /workspace/app/dist/*.whl /tmp/

WORKDIR /workspace/app

RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    uv venv /workspace/app/.venv \
    && uv pip install --quiet --no-cache-dir --no-deps --only-binary :all: --requirement=/tmp/requirements.txt \
    && uv pip install --quiet --no-cache-dir --no-deps --only-binary :all: /tmp/*.whl \
    && rm -rf /tmp/* \
    && chown -R nonroot:nonroot /workspace/app

USER nonroot

STOPSIGNAL SIGTERM
EXPOSE 8000

ENTRYPOINT ["tini", "--"]
CMD ["app", "run", "--host", "0.0.0.0"]

LABEL org.opencontainers.image.title="Litestar Fullstack SPA" \
      org.opencontainers.image.description="Python application container" \
      org.opencontainers.image.vendor="Litestar" \
      org.opencontainers.image.licenses="MIT"
