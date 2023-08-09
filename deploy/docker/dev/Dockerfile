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
## -------------------------- add build packages ----------------------------------- ##
RUN apt-get install -y --no-install-recommends build-essential curl \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && curl -sSL https://install.python-poetry.org | python - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

## -------------------------- install application ----------------------------------- ##
WORKDIR /workspace/app
COPY pyproject.toml poetry.lock README.md mkdocs.yml .pre-commit-config.yaml .pylintrc LICENSE Makefile \
    package.json package-lock.json vite.config.ts tsconfig.json \
    ./
COPY scripts ./scripts/
RUN python -m venv --copies /workspace/app/.venv \
    && /workspace/app/.venv/bin/pip install --quiet nodeenv cython  \
    && poetry install ${POETRY_INSTALL_ARGS} --no-root --quiet
COPY src ./src/

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
RUN poetry install $POETRY_INSTALL_ARGS
STOPSIGNAL SIGINT
EXPOSE 8000/tcp
ENTRYPOINT ["tini","--" ]
CMD [ "litestar","run"]
VOLUME /workspace/app
