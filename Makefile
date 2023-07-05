.DEFAULT_GOAL:=help
.ONESHELL:
ENV_PREFIX=$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")
USING_NPM=$(shell python3 -c "if __import__('pathlib').Path('package-lock.json').exists(): print('yes')")
VENV_EXISTS=$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/activate').exists(): print('yes')")
NODE_MODULES_EXISTS=$(shell python3 -c "if __import__('pathlib').Path('node_modules').exists(): print('yes')")
VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
SRC_DIR=src
BUILD_DIR=dist

.EXPORT_ALL_VARIABLES:

ifndef VERBOSE
.SILENT:
endif


help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


.PHONY: upgrade
upgrade:       ## Upgrade all dependencies to the latest stable versions
	@if [ "$(USING_POETRY)" ]; then poetry update; fi
	@echo "Python Dependencies Updated"
	@if [ "$(USING_NPM)" ]; then npm upgrade --latest; fi
	@echo "Node Dependencies Updated"
	$(ENV_PREFIX)pre-commit autoupdate
	@echo "Updated Pre-commit"

.PHONY: install
install:          ## Install the project in dev mode.
	@if ! poetry --version > /dev/null; then echo 'poetry is required, installing from from https://install.python-poetry.org'; curl -sSL https://install.python-poetry.org | python3 -; fi
	@if [ "$(VENV_EXISTS)" ]; then echo "Removing existing virtual environment"; fi
	@if [ "$(NODE_MODULES_EXISTS)" ]; then echo "Removing existing node environment"; fi
	if [ "$(VENV_EXISTS)" ]; then rm -Rf .venv; fi
	if [ "$(USING_POETRY)" ]; then poetry config virtualenvs.in-project true --local  && poetry config virtualenvs.options.always-copy true --local && python3 -m venv --copies .venv && . .venv/bin/activate && .venv/bin/pip install -U wheel setuptools cython pip && poetry install --with lint,dev,docs; fi
	if [ "$(USING_NPM)" ]; then npm ci; fi
	@echo "=> Install complete.  ** If you want to re-install re-run 'make install'"


.PHONY: migrations
migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will create a new database migration for any defined models changes."
	@while [ -z "$$MIGRATION_MESSAGE" ]; do read -r -p "Migration message: " MIGRATION_MESSAGE; done ;
	@env PYTHONPATH=src $(ENV_PREFIX)alembic -c src/app/lib/db/alembic.ini revision --autogenerate -m "$${MIGRATION_MESSAGE}"

.PHONY: migrate
migrate:          ## Generate database migrations
	@echo "ATTENTION: Will apply all database migrations."
	@env PYTHONPATH=src $(ENV_PREFIX)app database upgrade-database

.PHONY: squash-migrations
squash-migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will wipe all migrations and recreate from an empty state."
	@env PYTHONPATH=src $(ENV_PREFIX)app database purge-database --no-prompt
	rm -Rf src/app/lib/db/migrations/versions/*.py
	@while [ -z "$$MIGRATION_MESSAGE" ]; do read -r -p "Initial migration message: " MIGRATION_MESSAGE; done ;
	@env PYTHONPATH=src $(ENV_PREFIX)alembic -c src/app/lib/db/alembic.ini revision --autogenerate -m "$${MIGRATION_MESSAGE}"


.PHONY: build
build:
	@echo "=> Building package..."
	if [ "$(USING_POETRY)" ]; then poetry build; fi

.PHONY: test
test:
	@echo "=> Launching Python test cases..."
	$(ENV_PREFIX)pytest tests/

.PHONY: lint
lint:
	@echo "=> Executing pre-commit..."
	$(ENV_PREFIX)pre-commit run --all-files

gen-docs:       ## generate HTML documentation
	$(ENV_PREFIX)mkdocs build

.PHONY: docs
docs:       ## generate HTML documentation and serve it to the browser
	$(ENV_PREFIX)mkdocs build
	$(ENV_PREFIX)mkdocs serve

.PHONY: pre-release
pre-release:       ## bump the version and create the release tag
	make gen-docs
	make clean
	$(ENV_PREFIX)bump2version $(increment)
	git describe --tags --abbrev=0
	head pyproject.toml | grep version


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
