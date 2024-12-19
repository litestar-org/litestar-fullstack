ARG PYTHON_BUILDER_IMAGE=3.11-slim-bookworm

## ---------------------------------------------------------------------------------- ##
## ------------------------- Python base -------------------------------------------- ##
## ---------------------------------------------------------------------------------- ##
FROM python:${PYTHON_BUILDER_IMAGE} as python-base
ENV PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_NO_CACHE_DIR=1 \
  PIP_ROOT_USER_ACTION=ignore \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8
RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends git tini \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /root/.cache \
  && rm -rf /var/apt/lists/* \
  && rm -rf /var/cache/apt/* \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false\
  && mkdir -p /workspace/app \
  && pip install --quiet -U pip wheel setuptools virtualenv

## ---------------------------------------------------------------------------------- ##
## ------------------------- Python build base -------------------------------------- ##
## ---------------------------------------------------------------------------------- ##
FROM python-base AS build-base
ARG PDM_INSTALL_ARGS=""
ENV PDM_INSTALL_ARGS="${PDM_INSTALL_ARGS}" \
  GRPC_PYTHON_BUILD_WITH_CYTHON=1 \
  PATH="/workspace/app/.venv/bin:/usr/local/bin:$PATH"
## -------------------------- add build packages ----------------------------------- ##
RUN apt-get install -y --no-install-recommends build-essential curl \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /root/.cache \
  && rm -rf /var/apt/lists/* \
  && rm -rf /var/cache/apt/* \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false

## -------------------------- install application ----------------------------------- ##
WORKDIR /workspace/app
COPY pyproject.toml uv.lock README.md .pre-commit-config.yaml LICENSE Makefile \
  package.json package-lock.json vite.config.ts tsconfig.json tsconfig.node.json \
  tailwind.config.cjs postcss.config.cjs components.json \
  ./
COPY scripts ./scripts/
COPY public ./public/
COPY resources ./resources/
RUN python -m venv --copies /workspace/app/.venv \
  && /workspace/app/.venv/bin/pip install --quiet pdm nodeenv cython  \
  && pdm install ${PDM_INSTALL_ARGS} --no-self  \
  && pdm export ${PDM_INSTALL_ARGS} --without-hashes --prod --output=requirements.txt
COPY src ./src/
RUN pdm build


## ---------------------------------------------------------------------------------- ##
## -------------------------------- runtime build ----------------------------------- ##
## ---------------------------------------------------------------------------------- ##
## ------------------------- use base image  ---------------------------------------- ##

FROM python-base as run-image
ARG ENV_SECRETS="runtime-secrets"
ARG LITESTAR_APP="app.asgi:app"
ENV ENV_SECRETS="${ENV_SECRETS}" \
  LITESTAR_APP="${LITESTAR_APP}"

RUN addgroup --system --gid 65532 nonroot \
  && adduser --no-create-home --system --uid 65532 nonroot \
  && chown -R nonroot:nonroot /workspace
## -------------------------- install application ----------------------------------- ##
COPY --from=build-base --chown=65532:65532 /workspace/app/requirements.txt /tmp/requirements.txt
COPY --from=build-base --chown=65532:65532 /workspace/app/dist /tmp/
WORKDIR /workspace/app
RUN pip install --quiet --disable-pip-version-check --no-deps --requirement=/tmp/requirements.txt
RUN pip install --quiet --disable-pip-version-check --no-deps /tmp/*.whl

USER nonroot
STOPSIGNAL SIGINT
EXPOSE 8000
ENTRYPOINT ["tini","--" ]
CMD [ "litestar","run","--host","0.0.0.0"]
VOLUME /workspace/app
