ARG PYTHON_BUILDER_IMAGE=3.11-slim
ARG NODE_BUILDER_IMAGE=18-slim

## Build frontend
FROM node:${NODE_BUILDER_IMAGE} as ui-image
ARG STATIC_URL=/static/
ENV STATIC_URL="${STATIC_URL}"
WORKDIR /workspace/app
# RUN npm install -g npm@9.2.0
# COPY package.json package-lock.json angular.json tsconfig.json LICENSE Makefile ./
# RUN npm install
# COPY src/ui ./src/ui
# RUN npm run build

## Build venv
FROM python:${PYTHON_BUILDER_IMAGE} as python-base
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false
RUN pip install --upgrade pip wheel setuptools cython virtualenv

FROM python-base AS build-image
ARG POETRY_INSTALL_ARGS="--only main"
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_ALWAYS_COPY=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_VERSION='1.3.1' \
    POETRY_INSTALL_ARGS="${POETRY_INSTALL_ARGS}" \
    GRPC_PYTHON_BUILD_WITH_CYTHON=1 \
    PATH="/workspace/app/.venv/bin:$PATH"

RUN apt-get install -y --no-install-recommends curl git build-essential g++ unzip ca-certificates libaio1 libaio-dev ninja-build make gnupg cmake gcc libssl-dev wget zip maven unixodbc-dev libssl-dev libcurl4-gnutls-dev libexpat1-dev gettext checkinstall libffi-dev libz-dev \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false

# install poetry
RUN curl -sSL https://install.python-poetry.org | python - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# install application
WORKDIR /workspace/app
COPY pyproject.toml poetry.lock README.md mkdocs.yml mypy.ini .pre-commit-config.yaml .pylintrc LICENSE Makefile ./
COPY docs ./docs/
COPY scripts ./scripts
COPY tests ./tests/
COPY src ./src
RUN python -m venv --copies /workspace/app/.venv
RUN . /workspace/app/.venv/bin/activate \
    && pip install -U pip cython setuptools wheel \
    && poetry config virtualenvs.options.always-copy true \
    && poetry install $POETRY_INSTALL_ARGS
EXPOSE 8080



## Beginning of run image
FROM python:${PYTHON_BUILDER_IMAGE} as run-image
ARG ENV_SECRETS="runtime-secrets"
ENV PATH="/workspace/app/.venv/bin:$PATH" \
    ENV_SECRETS="${ENV_SECRETS}"
# switch to a non-root user for security

WORKDIR /workspace/app
RUN addgroup --system --gid 1001 "app-user" \
    && adduser --no-create-home --system --uid 1001 "app-user" \
    && chown -R "app-user":"app-user" /workspace
# move files that are changed more often towards the bottom or appended to the end for docker image caching
COPY --chown="app-user":"app-user" --from=build-image /workspace/app/.venv /workspace/app/.venv/
COPY --chown="app-user":"app-user" pyproject.toml README.md mkdocs.yml mypy.ini .pre-commit-config.yaml .pylintrc LICENSE Makefile ./
COPY --chown="app-user":"app-user" docs ./docs/
COPY --chown="app-user":"app-user" src /workspace/app/src
# COPY --chown="app-user":"app-user" --from=ui-image /workspace/app/src/ui/public /workspace/app/src/server/app/domain/web/public
USER "app-user"
STOPSIGNAL SIGINT
EXPOSE 8080
ENTRYPOINT [ "app" ]
CMD [ "run", "server"]
