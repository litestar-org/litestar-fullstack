SOURCES = app tests

.DEFAULT_GOAL := help
py = python -m poetry run

DOCKER_COMPOSE_FILE = contrib/docker-compose.yml
DOCKER_COMPOSE_PROJECT_NAME = easy

help: ## Display this help screen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

install: ## Install project dependencies
	python -m poetry install --no-interaction --no-ansi
.PHONY: install

format: ## Format the source code
	$(py) ruff check --config pyproject.toml --fix $(SOURCES)
	$(py) ruff format --config pyproject.toml $(SOURCES)
.PHONY: format

lint: ## Lint the source code
	$(py) ruff check --config pyproject.toml  $(SOURCES)
	$(py) mypy $(SOURCES)
	$(py) bandit -r app
.PHONY: lint

test: ## Run tests
	$(py) pytest -s -vvv -o log_cli=true -o log_cli_level=DEBUG
.PHONY: test

compose-up: ## Run the development server with docker-compose
	COMPOSE_PROJECT_NAME=${DOCKER_COMPOSE_PROJECT_NAME} docker-compose -f ${DOCKER_COMPOSE_FILE} up --build --no-deps --remove-orphans --force-recreate -d
.PHONY: compose-up

compose-down: ## Stop the development server with docker-compose
	COMPOSE_PROJECT_NAME=${DOCKER_COMPOSE_PROJECT_NAME} docker-compose -f ${DOCKER_COMPOSE_FILE} down -v --remove-orphans
.PHONY: compose-down

.PHONY: migrate ## Upgrade the database to the latest revision
migrate:
	$(py) alembic upgrade head

.PHONY: migration-downgrade
migration-downgrade:  ## Downgrade the database to the previous revision
	$(py) alembic downgrade -1

.PHONY: run-web
run-web: ## Run the web server
	$(py) python app/asgi.py

.PHONY: run-worker
run-worker: ## Run Uvicorn worker
	$(py) gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.asgi:fastapi_app --bind 0.0.0.0:8000 --timeout 300 --log-level debug