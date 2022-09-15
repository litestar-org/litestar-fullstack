#!/usr/bin/env bash
poetry run isort --force-single-line-imports src --skip migrations,.venv
poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place src --exclude '/(\.direnv|\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist|\.venv|node_modules|__init__)/'
poetry run isort src --skip .venv,migrations
poetry run black src --exclude '/(\.direnv|\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist|\.venv|node_modules|migrations)/'
