SHELL := /bin/bash
# =============================================================================
# Variables
# =============================================================================

.DEFAULT_GOAL:=help
.ONESHELL:
USING_NPM             		= $(shell python3 -c "if __import__('pathlib').Path('package-lock.json').exists(): print('yes')")
ENV_PREFIX		        	=.venv/bin/
NODE_MODULES_EXISTS			=	$(shell python3 -c "if __import__('pathlib').Path('node_modules').exists(): print('yes')")
SRC_DIR               		=src
BUILD_DIR             		=dist

.EXPORT_ALL_VARIABLES:

ifndef VERBOSE
.SILENT:
endif


.PHONY: help
help: 		   										## Display this help text for Makefile
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


.PHONY: upgrade
upgrade:       										## Upgrade all dependencies to the latest stable versions
	@echo "=> Updating all dependencies"
	@uv lock --upgrade
	@echo "=> Python Dependencies Updated"
	@if [ "$(USING_NPM)" ]; then npm upgrade --latest; fi
	@echo "=> Node Dependencies Updated"
	@$(ENV_PREFIX)pre-commit autoupdate
	@echo "=> Updated Pre-commit"

# =============================================================================
# Developer Utils
# =============================================================================
install:											## Install the project and
	@uv sync
	@if [ "$(NODE_MODULES_EXISTS)" ]; then echo "=> Removing existing node modules"; fi
	if [ "$(NODE_MODULES_EXISTS)" ]; then $(MAKE) destroy-node_modules; fi
	@echo "=> Install complete! Note: If you want to re-install re-run 'make install'"


clean: 												## Cleanup temporary build artifacts
	@echo "=> Cleaning working directory"
	@rm -rf .pytest_cache .ruff_cache .hypothesis build/ -rf dist/ .eggs/ .coverage coverage.xml coverage.json htmlcov/ .mypy_cache
	@find . -name '*.egg-info' -exec rm -rf {} +
	@find . -name '*.egg' -exec rm -f {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '.pytest_cache' -exec rm -rf {} +
	@find . -name '.ipynb_checkpoints' -exec rm -rf {} +

destroy-venv: 											## Destroy the virtual environment
	@echo "=> Cleaning Python virtual environment"
	@rm -rf .venv

destroy-node_modules: 											## Destroy the node environment
	@echo "=> Cleaning Node modules"
	@rm -rf node_modules

tidy: clean destroy-venv destroy-node_modules ## Clean up everything

migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will create a new database migration for any defined models changes."
	@while [ -z "$$MIGRATION_MESSAGE" ]; do read -r -p "Migration message: " MIGRATION_MESSAGE; done ;
	@$(ENV_PREFIX)app database make-migrations --autogenerate -m "$${MIGRATION_MESSAGE}"

.PHONY: migrate
migrate:          ## Generate database migrations
	@echo "ATTENTION: Will apply all database migrations."
	@$(ENV_PREFIX)app database upgrade

.PHONY: build
build:
	@echo "=> Building package..."
	@uv build
	@echo "=> Package build complete..."

.PHONY: lock
lock:                                             ## Rebuild lockfiles from scratch, updating all dependencies
	@uv lock

start-infra:
	docker compose -f docker-compose.infra.yml up --force-recreate -d

stop-infra:
	docker compose -f docker-compose.infra.yml down --remove-orphans

post_install:
	pdm run python scripts/pre-build.py --install-packages

pre_build:
	pdm run python scripts/pre-build.py --build-assets
# =============================================================================
# Tests, Linting, Coverage
# =============================================================================
.PHONY: lint
lint: 												## Runs pre-commit hooks; includes ruff linting, codespell, black
	@echo "=> Running pre-commit process"
	@$(ENV_PREFIX)pre-commit run --all-files
	@echo "=> Pre-commit complete"

.PHONY: format
format: 												## Runs code formatting utilities
	@echo "=> Running pre-commit process"
	@$(ENV_PREFIX)ruff . --fix
	@echo "=> Pre-commit complete"

.PHONY: coverage
coverage:  											## Run the tests and generate coverage report
	@echo "=> Running tests with coverage"
	@$(ENV_PREFIX)pytest tests --cov=app
	@$(ENV_PREFIX)coverage html
	@$(ENV_PREFIX)coverage xml
	@echo "=> Coverage report generated"

.PHONY: test
test:  												## Run the tests
	@echo "=> Running test cases"
	@$(ENV_PREFIX)pytest tests
	@echo "=> Tests complete"

# =============================================================================
# Docs
# =============================================================================
.PHONY: docs-install
docs-install: 										## Install docs dependencies
	@echo "=> Installing documentation dependencies"
	@uv sync --group docs
	@echo "=> Installed documentation dependencies"

docs-clean: 										## Dump the existing built docs
	@echo "=> Cleaning documentation build assets"
	@rm -rf docs/_build
	@echo "=> Removed existing documentation build assets"

docs-serve: docs-clean 								## Serve the docs locally
	@echo "=> Serving documentation"
	$uv run sphinx-autobuild docs docs/_build/ -j auto --watch src --watch docs --watch tests --watch CONTRIBUTING.rst --port 8002

docs: docs-clean 									## Dump the existing built docs and rebuild them
	@echo "=> Building documentation"
	@uv run sphinx-build -M html docs docs/_build/ -E -a -j auto --keep-going
