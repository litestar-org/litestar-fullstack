
ARG BUILDER_IMAGE=python:3.13-slim-bookworm
## ---------------------------------------------------------------------------------- ##
## ------------------------- Python base -------------------------------------------- ##
## ---------------------------------------------------------------------------------- ##
FROM ${BUILDER_IMAGE} AS python-base
RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends tini \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /root/.cache \
  && rm -rf /var/apt/lists/* \
  && rm -rf /var/cache/apt/* \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && mkdir -p /workspace/app
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
## ---------------------------------------------------------------------------------- ##
## ------------------------- Python build base -------------------------------------- ##
## ---------------------------------------------------------------------------------- ##
FROM python-base AS builder
ARG UV_INSTALL_ARGS="--no-dev"
ENV GRPC_PYTHON_BUILD_WITH_CYTHON=1 \
  UV_LINK_MODE=copy \
  UV_NO_CACHE=1 \
  UV_COMPILE_BYTECODE=1 \
  UV_INSTALL_ARGS="${UV_INSTALL_ARGS}" \
  UV_SYSTEM_PYTHON=1 \
  PATH="/workspace/app/.venv/bin:/usr/local/bin:/opt/nodeenv/bin:$PATH" \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8
## -------------------------- add build packages ----------------------------------- ##
RUN apt-get install -y --no-install-recommends git build-essential curl \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /root/.cache \
  && rm -rf /var/apt/lists/* \
  && rm -rf /var/cache/apt/* \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && mkdir -p /cloudsql


## -------------------------- install application ----------------------------------- ##
WORKDIR /workspace/app
COPY pyproject.toml uv.lock README.md .pre-commit-config.yaml LICENSE Makefile \
  package.json package-lock.json vite.config.ts tsconfig.json \
  tailwind.config.cjs postcss.config.cjs components.json \
  ./
COPY tools ./tools/
RUN uvx nodeenv --quiet /opt/nodeenv/
RUN NODE_OPTIONS="--no-deprecation --disable-warning=ExperimentalWarning" npm install --ignore-scripts --no-fund
RUN uv venv \
  && uv sync ${UV_INSTALL_ARGS} --frozen --no-install-project --no-editable \
  && uv export ${UV_INSTALL_ARGS} --frozen --no-hashes --output-file=requirements.txt

COPY public ./public/
COPY resources ./resources/
RUN uv run pip install --quiet cython \
  && uv sync ${UV_INSTALL_ARGS} --frozen --no-install-project --no-editable \
  && uv export ${UV_INSTALL_ARGS} --frozen --no-hashes --output-file=requirements.txt \
  --no-emit-workspace --no-group dev --no-group test --no-group linting --no-group docs
COPY src ./src/

# build the frontend and sync the project
RUN uv run tools/manage_assets.py --build-assets \
  && uv sync ${UV_INSTALL_ARGS} --frozen --no-editable \
  && uv build


## ---------------------------------------------------------------------------------- ##
## -------------------------------- Run Image     ----------------------------------- ##
## ---------------------------------------------------------------------------------- ##
## ------------------------- use base image  ---------------------------------------- ##

FROM python-base AS runner
ARG ENV_SECRETS="runtime-secrets"
ARG VITE_USE_SERVER_LIFESPAN="false"
ARG SAQ_USE_SERVER_LIFESPAN="false"
ARG LITESTAR_APP="app.asgi:create_app"
ENV ENV_SECRETS="${ENV_SECRETS}" \
  PATH="/workspace/app/.venv/bin:/usr/local/bin:$PATH" \
  UV_LINK_MODE=copy \
  UV_NO_CACHE=1 \
  UV_COMPILE_BYTECODE=1 \
  UV_SYSTEM_PYTHON=1 \
  UV_INSTALL_ARGS="${UV_INSTALL_ARGS}" \
  VITE_USE_SERVER_LIFESPAN="${VITE_USE_SERVER_LIFESPAN}" \
  SAQ_USE_SERVER_LIFESPAN="${SAQ_USE_SERVER_LIFESPAN}" \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  LITESTAR_APP="${LITESTAR_APP}"
## -------------------------- install built application -------------------------------- ##
RUN addgroup --system --gid 65532 nonroot \
  && adduser --no-create-home --system --uid 65532 nonroot \
  && chown -R nonroot:nonroot /workspace
COPY --from=builder --chown=65532:65532 /cloudsql /cloudsql
COPY --from=builder --chown=65532:65532 /workspace/app/dist /tmp/
COPY --from=builder --chown=65532:65532 /workspace/app/requirements.txt /tmp/
WORKDIR /workspace/app
RUN uv pip ${UV_INSTALL_ARGS} install --quiet --disable-pip-version-check /tmp/*.whl --no-deps \
  && uv pip ${UV_INSTALL_ARGS} install -r /tmp/requirements.txt \
  && rm -Rf /tmp/* \
  && chown -R nonroot:nonroot /workspace/app
USER nonroot
STOPSIGNAL SIGINT
EXPOSE 8000
ENTRYPOINT ["tini","--" ]
CMD [ "app", "run", "--port","8000", "--host", "0.0.0.0"]
VOLUME /workspace/app
