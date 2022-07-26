# Workflows

## Test

- Run the tests on every push/pull_request to the *main* branch.
- Writes a coverage report using pytest-cov and uploads it to codecov.io.
- Tests run against python versions 3.8 and 3.9.
- Optional manual trigger in the github actions tab.

## Lint

- Run the linting tools on every push/pull_request to the *main* branch.
- Includes pre-commit hooks, black, isort, flake8, pylint, and mypy.
- Optional manual trigger in the github actions tab.

## Release

- Build a wheel distribution, build a docker image, create a github release, and publish to PyPI and Docker Hub whenever a new tag is created.
- Linting and testing steps must pass before the release steps can begin.
- Documentation is automatically published to the *docs* branch and hosted on github pages.
- All github release tags, docker image tags, and PyPI version numbers are in agreement with one another and follow semantic versioning standards.

## Build and Publish Docs

- Build the documentation, publish to the *docs* branch, and release to github pages.
- Runs only on a manual trigger in the github actions tab.

## Build and Publish Docker Image

- Build the docker image, tag it with the branch name, and publish it to dockerhub.
- Runs only a manual trigger in the github actions tab.
