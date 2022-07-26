# Dockerfile
ARG PYTHON_BUILDER_IMAGE=3.10-slim
ARG NODE_BUILDER_IMAGE=18-slim

## Node image for JS applications
FROM node:${NODE_BUILDER_IMAGE} as node-base
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get autoremove -y
# todo: add build commands here

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
    && rm -rf /var/cache/apt/*
RUN pip install --no-cache-dir --upgrade pip  \
    pip install --no-cache-dir wheel setuptools virtualenv


FROM python-base AS build-stage
ARG POETRY_INSTALL_ARGS="--no-dev"
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_ALWAYS_COPY=1 \
    POETRY_VERSION='1.1.4' \
    POETRY_INSTALL_ARGS="${POETRY_INSTALL_ARGS}" 
RUN apt-get install -y --no-install-recommends curl git build-essential \
    && apt-get autoremove -y

RUN curl -sSL https://install.python-poetry.org | python \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root ${POETRY_INSTALL_ARGS}

## Store the commit versiom into the image for usage later
FROM alpine/git AS git
ADD . /app
WORKDIR /app
# Use this file to provide the git commit
# in the footer without having git present
# in my production image
RUN git rev-parse HEAD | tee /version

## Beginning of runtime image
FROM python:${PYTHON_BUILDER_IMAGE} as run-image
COPY --from=build-stage /app/venv /app/venv/
ENV PATH /app/venv/bin:$PATH
WORKDIR /app
COPY LICENSE pyproject.toml ./
COPY alembic.ini ./
COPY scripts ./scripts/
COPY alembic ./alembic/
# These are the two folders that change the most.
COPY pyspa ./app/
COPY --from=git /version /app/.version

# switch to a non-root user for security
RUN addgroup --system --gid 1001 "app-user"
RUN adduser --system --uid 1001 "app-user"
USER "app-user"