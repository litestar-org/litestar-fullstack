.DEFAULT_GOAL:=help
.ONESHELL:
ENV_PREFIX=$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")
USING_DOCKER=$(shell grep "USE_DOCKER=true" .env && echo "yes")
USING_PNPM=$(shell python3 -c "if __import__('pathlib').Path('pnpm-lock.yaml').exists(): print('yes')")
USING_YARN=$(shell python3 -c "if __import__('pathlib').Path('yarn.lock').exists(): print('yes')")
USING_NPM=$(shell python3 -c "if __import__('pathlib').Path('package-lock.json').exists(): print('yes')")
VENV_EXISTS=$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/activate').exists(): print('yes')")
NODE_MODULES_EXISTS=$(shell python3 -c "if __import__('pathlib').Path('node_modules').exists(): print('yes')")
PYTHON_PACKAGES=$(shell if poetry --version > /dev/null; then poetry export -f requirements.txt  --without-hashes |cut -d'=' -f1 |cut -d ' ' -f1; fi)
VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
FRONTEND_SRC_DIR=src/ui
FRONTEND_BUILD_DIR=$(FRONTEND_SRC_DIR)/dist
BACKEND_SRC_DIR=src/server
BACKEND_BUILD_DIR=dist

.EXPORT_ALL_VARIABLES:

ifndef VERBOSE
.SILENT:
endif


REPO_INFO ?= $(shell git config --get remote.origin.url)
COMMIT_SHA ?= git-$(shell git rev-parse --short HEAD)

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


.PHONY: upgrade
upgrade:       ## Upgrade all dependencies to the latest stable versions
	@if [ "$(USING_POETRY)" ]; then poetry update; fi
	@echo "Python Dependencies Updated"
	@if [ "$(USING_NPM)" ]; then npm upgrade --latest; fi
	@if [ "$(USING_YARN)" ]; then yarn upgrade; fi
	@if [ "$(USING_PNPM)" ]; then pnpm upgrade --latest; fi
	@echo "Node Dependencies Updated"

###############
# lint & test #
###############
lint:       ## check style with flake8
	env PYTHONPATH=src/server poetry run pre-commit run --all-files

test:       ## run tests quickly with the default Python
	env PYTHONPATH=src/server poetry run pytest --cov-config .coveragerc --cov=src -l --tb=short tests/server/unit
	env PYTHONPATH=src/server poetry run coverage xml
	env PYTHONPATH=src/server poetry run coverage html

coverage:       ## check code coverage quickly with the default Python
	env PYTHONPATH=src/server poetry run coverage run --source app -m pytest
	env PYTHONPATH=src/server poetry run coverage report -m


###############
# app         #
###############
.PHONY: install
install:          ## Install the project in dev mode.
	@if ! poetry --version > /dev/null; then echo 'poetry is required, installing from from https://install.python-poetry.org'; curl -sSL https://install.python-poetry.org | python3 -; fi
	@if [ "$(VENV_EXISTS)" ]; then echo "Removing existing virtual environment"; fi
	@if [ "$(NODE_MODULES_EXISTS)" ]; then echo "Removing existing node environment"; fi
	if [ "$(VENV_EXISTS)" ]; then rm -Rf .venv; fi
	if [ "$(USING_POETRY)" ]; then poetry config virtualenvs.in-project true  && poetry config virtualenvs.options.always-copy true && python3 -m venv .venv && source .venv/bin/activate && .venv/bin/pip install -U wheel setuptools cython pip && poetry install --with lint,dev,docs && mkdir -p ./src/ui/public; fi
	if [ "$(USING_NPM)" ]; then npm install; fi
	if [ "$(USING_YARN)" ]; then yarn install; fi
	if [ "$(USING_PNPM)" ]; then pnpm install; fi
	@echo "=> Install complete.  ** If you want to re-install re-run 'make install'"



.PHONY: runtime
runtime-only:	 ## Install the project in production mode.
	@if ! poetry --version > /dev/null; then echo 'poetry is required, installing from from https://install.python-poetry.org'; curl -sSL https://install.python-poetry.org | python3 -; fi
	@if [ "$(VENV_EXISTS)" ]; then echo "Removing existing environment"; fi
	if [ "$(VENV_EXISTS)" ]; then rm -Rf .venv; fi
	if [ "$(USING_POETRY)" ]; then poetry config virtualenvs.in-project true  && poetry config virtualenvs.options.always-copy true && python3 -m venv .venv && source .venv/bin/activate && .venv/bin/pip install -U wheel setuptools cython pip && poetry install --only main && mkdir -p ./src/ui/public ; fi
	if [ "$(USING_NPM)" ]; then npm install; fi
	@echo "=> Install complete.  ** If you want to re-install re-run 'make runtime'"

.PHONY: migrations
migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will create a new database migration for any defined models changes."
	@while [ -z "$$MIGRATION_MESSAGE" ]; do read -r -p "Migration message: " MIGRATION_MESSAGE; done ;
	@env PYTHONPATH=src poetry run alembic -c src/server/app/lib/db/alembic.ini revision --autogenerate -m "$${MIGRATION_MESSAGE}"

.PHONY: migrate
migrate:          ## Generate database migrations
	@echo "ATTENTION: Will apply all database migrations."
	@env PYTHONPATH=src/server .venv/bin/app manage upgrade-database

.PHONY: squash-migrations
squash-migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will wipe all migrations and recreate from an empty state."
	@env PYTHONPATH=src/server poetry run app manage purge-database --no-prompt
	rm -Rf src/server/app/lib/db/migrations/versions/*.py
	@while [ -z "$$MIGRATION_MESSAGE" ]; do read -r -p "Initial migration message: " MIGRATION_MESSAGE; done ;
	@env PYTHONPATH=src .venv/bin/alembic -c src/server/app/lib/db/alembic.ini revision --autogenerate -m "$${MIGRATION_MESSAGE}"

.PHONY: clean
clean:       ## remove all build, testing, and static documentation files
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.ipynb_checkpoints' -exec rm -fr {} +
	rm -fr .tox/
	rm -fr .coverage
	rm -fr coverage.xml
	rm -fr coverage.json
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -fr .mypy_cache
	rm -fr site


download-backend-deps:      ## download wheel files
	@poetry export --without-hashes --only=main -f requirements.txt --output dist/requirements.txt && rm -Rf dist/wheels && poetry run pip download --no-binary=':all:'  -r dist/requirements.txt -d dist/wheels

build-frontend: $(FRONTEND_BUILD_DIR)

$(FRONTEND_BUILD_DIR): $(shell find $(FRONTEND_SRC_DIR) -not -path "$(FRONTEND_BUILD_DIR)")
	@poetry run app manage export-openapi-schema --export-path ./src/ui/spec/
	@npm run build

build-backend: $(BACKEND_BUILD_DIR)

$(BACKEND_BUILD_DIR): $(shell find $(BACKEND_SRC_DIR))
	@poetry build

build: build-frontend build-backend          ## Install the project in dev mode.

###############
# docs        #
###############
gen-docs:       ## generate HTML documentation
	.venv/bin/mkdocs build

.PHONY: docs
docs:       ## generate HTML documentation and serve it to the browser
	.venv/bin/mkdocs build
	.venv/bin/mkdocs serve

.PHONY: pre-release
pre-release:       ## bump the version and create the release tag
	make gen-docs
	make clean
	.venv/bin/bump2version $(increment)
	git describe --tags --abbrev=0
	head pyproject.toml | grep version
