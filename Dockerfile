# Dockerfile
ARG PYTHON_BUILDER_IMAGE=3.10-slim
ARG NODE_BUILDER_IMAGE=18-slim
## Store the commit versiom into the image for usage later
FROM docker.io/alpine/git AS git
ADD . /workspace/app
WORKDIR /workspace/app
# I use this file to provide the git commit
# in the footer without having git present
# in my production image
RUN git rev-parse HEAD | tee /version

## Node image for JS applications
FROM node:${NODE_BUILDER_IMAGE} as node-base
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/*
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
    && rm -rf /var/cache/apt/* \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false
RUN pip install --upgrade pip wheel setuptools cython virtualenv numpy


FROM python-base AS build-stage
ARG POETRY_INSTALL_ARGS="--only main"
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_VERSION='1.2.1' \
    POETRY_INSTALL_ARGS="${POETRY_INSTALL_ARGS}" \
    PROTOC_VERSION="3.14.0" \
    BAZEL_VERSION="5.1.1" \
    GRPC_PYTHON_BUILD_WITH_CYTHON=1

RUN apt-get install -y --no-install-recommends curl git build-essential g++ unzip ca-certificates libaio1 libaio-dev ninja-build make cmake gcc libssl-dev wget zip maven unixodbc-dev libssl-dev libcurl4-gnutls-dev libexpat1-dev gettext checkinstall libffi-dev libz-dev \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false

# installs specified bazel
RUN if [ `uname -m` = 'x86_64' ]; then BAZEL_ARCHITECTURE="x86_64"; else BAZEL_ARCHITECTURE="arm64"; fi \
    && curl -sS -L -o bazel --output-dir /usr/local/bin/ --create-dirs "https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-linux-${BAZEL_ARCHITECTURE}" \
    && chmod +x /usr/local/bin/bazel 

# installs specified protobuf 
RUN if [ `uname -m` = 'x86_64' ]; then PROTOC_ARCHITECTURE="x86_64"; else PROTOC_ARCHITECTURE="aarch_64"; fi \
    && curl -sS -L -o protoc.zip --output-dir /tmp/ --create-dirs "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-${PROTOC_ARCHITECTURE}.zip" \
    && unzip /tmp/protoc.zip -d /usr/local \
    && rm -rf /tmp/*


# installs latest instant client
RUN if [ `uname -m` = 'x86_64' ]; then ORA_ARCHITECTURE="x64"; else ORA_ARCHITECTURE="arm64"; fi \
    && mkdir -p /usr/share/oracle/network/admin \
    && cd /usr/share/oracle \
    && curl -sS -L -o instantclient.zip --output-dir /usr/share/oracle/ https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linux-${ORA_ARCHITECTURE}.zip \
    && unzip /usr/share/oracle/instantclient.zip \
    && rm -f instantclient.zip \
    && cd  /usr/share/oracle/instantclient* \
    && rm -f *jdbc* *occi* *mysql* *README *jar uidrvci genezi adrci \
    && echo  /usr/share/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig

RUN curl -sSL https://install.python-poetry.org | python - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

WORKDIR /workspace/app
COPY pyproject.toml poetry.lock README.md mkdocs.yml mypy.ini .flake8 .pre-commit-config.yaml .pylintrc LICENSE NOTICE Makefile ./
RUN python -m venv --copies /workspace/venv
RUN . /workspace/venv/bin/activate \
    && pip install -U cython setuptools wheel numpy \
    && poetry install $POETRY_INSTALL_ARGS
COPY   tools ./tools/
COPY   docs ./docs/
COPY   tools ./tools/
COPY   notebooks ./notebooks/


## Beginning of runtime image
FROM python:${PYTHON_BUILDER_IMAGE} as run-image
ENV PATH /workspace/venv/bin:$PATH
# switch to a non-root user for security
RUN addgroup --system --gid 1001 "app-user" \
    && adduser --no-create-home --system --uid 1001 "app-user" \
    && chown -R "app-user":"app-user" /workspace
# move files that are changed more often towards the bottom or appended to the end for docker image caching
COPY --chown="app-user":"app-user" --from=build-stage /workspace/venv /workspace/venv/
COPY --chown="app-user":"app-user" --from=git /version /workspace/app/.version
COPY --chown="app-user":"app-user" LICENSE NOTICE ./
COPY --chown="app-user":"app-user" docs ./docs/
COPY --chown="app-user":"app-user"  pyproject.toml README.md mkdocs.yml mypy.ini .flake8 .pre-commit-config.yaml .pylintrc Makefile ./
COPY --chown="app-user":"app-user" --from=build-stage /workspace/venv /workspace/venv/
# this folder changes the most
COPY --chown="app-user":"app-user" src /workspace/app/src

USER "app-user"
ENTRYPOINT [ "app","run", "server"]
EXPOSE 8080
