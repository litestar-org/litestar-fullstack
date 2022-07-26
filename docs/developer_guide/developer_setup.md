# Developer Setup

To begin local development, clone the [PyTemplates/typer_cli](https://github.com/PyTemplate/typer_cli) repository and use one of the following methods to build it. Commands should be executed from inside of the project home folder.

## Using poetry

```bash
poetry install
```

Install optional dependencies using the `--extras` flag:

```bash
poetry install --extras=environment
```

## Using pip

```bash
pip install .
```

Install optional dependencies using square brackets:

```bash
pip install .[environment]
```

## Environments

```python
test = [
    "pytest",
    "pytest-cov",
]

lint = [
    "black",
    "isort",
    "flake8",
    "pylint",
    "mypy",
    "pre-commit",
]

docs = [
    "mkdocs",
    "mkdocstrings",
    "mkdocstrings-python",
    "mkdocs-material",
]

# Includes all optional dependencies
dev = [
    "pytest",
    "pytest-cov",
    "black",
    "isort",
    "flake8",
    "pylint",
    "mypy",
    "pre-commit",
    "mkdocs",
    "mkdocstrings",
    "mkdocstrings-python",
    "mkdocs-material",
    "bump2version",
]
```

## Using a local docker build

To build an image locally from the Dockerfile:

```bash
make build
```

To run the image:

```bash
docker run --rm pyvite hello user
docker run --rm pyvite goodbye user
docker run --rm pyvite version
```
