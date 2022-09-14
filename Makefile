.DEFAULT_GOAL:=help
.ONESHELL:
ENV_PREFIX=$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")
USING_DOCKER=$(shell grep "OPDBA_USE_DOCKER=true" .env && echo "yes")
USING_PNPM=$(shell python3 -c "if __import__('pathlib').Path('pnpm-lock.yaml').exists(): print('yes')")
USING_YARN=$(shell python3 -c "if __import__('pathlib').Path('yarn.lock').exists(): print('yes')")
USING_NPM=$(shell python3 -c "if __import__('pathlib').Path('package-lock.json').exists(): print('yes')")
VENV_EXISTS=$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/activate').exists(): print('yes')")
PYTHON_PACKAGES=$(shell poetry export -f requirements.txt  --without-hashes |cut -d'=' -f1 |cut -d ' ' -f1)
GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1
.EXPORT_ALL_VARIABLES:

ifndef VERBOSE
.SILENT:
endif


REPO_INFO ?= $(shell git config --get remote.origin.url)
COMMIT_SHA ?= git-$(shell git rev-parse --short HEAD)

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


.PHONY: upgrade-dependencies
upgrade-dependencies:          ## Upgrade all dependencies to the latest stable versions
	@if [ "$(USING_POETRY)" ]; then poetry update; fi
	@echo "Python Dependencies Updated"
	@if [ "$(USING_YARN)" ]; then yarn upgrade; fi
	@if [ "$(USING_PNPM)" ]; then pnpm upgrade; fi
	@echo "Node Dependencies Updated"

###############
# lint & test #
###############
format-source: ## Format source code
	@echo 'Formatting and cleaning source...'
	./scripts/format-source-code.sh

lint: ## check style with flake8
	env PYTHONPATH=src poetry run flake8 src

test: ## run tests quickly with the default Python
	env PYTHONPATH=src poetry run pytest --cov-config .coveragerc --cov=src -l --tb=short tests/backend/unit
	coverage xml
	coverage html

test-all: ## run tests on every Python version with tox
	env PYTHONPATH=src poetry run tox

coverage: ## check code coverage quickly with the default Python
	env PYTHONPATH=src/ poetry run coverage run --source pyspa -m pytest
	env PYTHONPATH=src/ poetry run coverage report -m

.PHONY: install
install:          ## Install the project in dev mode.
	@if ! poetry --version > /dev/null; then echo 'poetry is required, install from https://python-poetry.org/'; exit 1; fi
	@if [ "$(VENV_EXISTS)" ]; then echo "Removing existing environment"; fi
	@if [ "$(VENV_EXISTS)" ]; then rm -Rf .venv; fi
	@if [ "$(USING_POETRY)" ]; then poetry config virtualenvs.in-project true && poetry config virtualenvs.create true && poetry config virtualenvs.options.always-copy true && poetry install && exit; fi
	@if [ "$(USING_NPM)" ]; then npm install; fi
	@echo "Install complete.  ** If you want to recreate your entire virtualenv run 'make virtualenv'"


.PHONY: migrations
migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will create a new database migration for any defined models changes."
	@env PYTHONPATH=src poetry run alembic -c src/pyspa/config/alembic.ini revision --autogenerate -m "$${MIGRATION_MESSAGE}"

.PHONY: migrate
migrate:          ## Generate database migrations
	@echo "ATTENTION: Will apply all database migrations."
	@env PYTHONPATH=src poetry run pyspa config upgrade-database

.PHONY: squash-migrations
squash-migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will wipe alll migrations and recreate from an emtpy state."
	@env PYTHONPATH=src poetry run pyspa config purge-database --no-prompt
	rm -Rf src/pyspa/db/migrations/versions/*.py
	@env PYTHONPATH=src poetry run alembic -c src/pyspa/config/alembic.ini revision --autogenerate -m "$${MIGRATION_MESSAGE}"

