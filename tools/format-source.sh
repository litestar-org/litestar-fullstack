#!/usr/bin/env bash
poetry run isort --force-single-line-imports src/server --skip migrations,.venv
poetry run isort --force-single-line-imports tests/server --skip migrations,.venv

poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place src/server --exclude '/(\.direnv|\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist|\.venv|node_modules|__init__)/'
poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place tests/server --exclude '/(\.direnv|\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist|\.venv|node_modules|__init__)/'

poetry run isort src/server --skip .venv,migrations
poetry run isort tests/server --skip .venv,migrations

poetry run black src/server --exclude '/(\.direnv|\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist|\.venv|node_modules|migrations)/'
poetry run black tests/server --exclude '/(\.direnv|\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist|\.venv|node_modules|migrations)/'
