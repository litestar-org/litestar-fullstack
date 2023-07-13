ARG PYTHON_BUILDER_IMAGE=3.11-slim-bookworm

## ---------------------------------------------------------------------------------- ##
## ------------------------- Python base -------------------------------------------- ##
## ---------------------------------------------------------------------------------- ##
FROM python:${PYTHON_BUILDER_IMAGE} as python-base
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    APPLICATION_RUN_TYPE=development
WORKDIR /workspace/app

## -------------------------- add common compiled libraries --------------------------- ##
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends git tini openssh-server \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false
RUN mkdir -p /workspace/app \
    && addgroup --system --gid 65532 nonroot \
    && adduser --no-create-home --system --uid 65532 nonroot \
    && chown -R nonroot:nonroot /workspace

## ---------------------------------------------------------------------------------- ##
## ------------------------- Python build base -------------------------------------- ##
## ---------------------------------------------------------------------------------- ##
FROM python-base AS build-base
ARG POETRY_INSTALL_ARGS="--only main"
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_ALWAYS_COPY=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_VERSION='1.5.1' \
    POETRY_INSTALL_ARGS="${POETRY_INSTALL_ARGS}" \
    GRPC_PYTHON_BUILD_WITH_CYTHON=1 \
    PATH="/workspace/app/.venv/bin:/usr/local/bin:$PATH"
## -------------------------- add development packages ------------------------------ ##
RUN apt-get install -y --no-install-recommends build-essential curl \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false

## -------------------------- install application ----------------------------------- ##
WORKDIR /workspace/app
RUN curl -sSL https://install.python-poetry.org | python - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry
COPY pyproject.toml poetry.lock README.md mkdocs.yml mypy.ini .pre-commit-config.yaml .pylintrc LICENSE Makefile \
    package.json package-lock.json vite.config.ts tsconfig.json \
    ./
RUN python -m venv --copies /workspace/app/.venv
COPY scripts ./scripts/
RUN /workspace/app/.venv/bin/pip install -U cython nodeenv \
    && poetry install $POETRY_INSTALL_ARGS --no-root

## ---------------------------------------------------------------------------------- ##
## -------------------------------- development build ------------------------------- ##
## ---------------------------------------------------------------------------------- ##
## ------------------------- use builder base --------------------------------------- ##
FROM build-base as dev-image
ARG ENV_SECRETS="runtime-secrets"
## --------------------------- standardize execution env ----------------------------- ##
ENV PATH="/workspace/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/workspace/app/.venv" \
    ENV_SECRETS="${ENV_SECRETS}"  \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
WORKDIR /workspace/app
COPY docs/ docs/
COPY tests/ tests/
COPY src src/
COPY ssh_files/ ssh_files/
#
RUN chmod 400 /workspace/app/ssh_files/.ssh/id_rsa_gitlab \
  && chmod +x /workspace/app/ssh_files/create_development_ssh_tunnel.sh \
  && /workspace/app/ssh_files/create_development_ssh_tunnel.sh

RUN poetry install $POETRY_INSTALL_ARGS
STOPSIGNAL SIGINT
EXPOSE 8000/tcp
ENTRYPOINT ["tini","--" ]
CMD [ "litestar","run"]
VOLUME /workspace/app
