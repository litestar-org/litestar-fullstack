# Commands

- `make clean` - Remove all build, testing, and static documentation files.

- `make test` - Run the tests using pytest.

- `make lint` - Run the linting tools. Includes pre-commit hooks, black, isort, flake8, pylint, and mypy.

- `make check` - Run the test and lint commands.

- `make build` - Build a docker image locally using the Dockerfile. The image will be named _pyvite_.

- `make gen-docs` - Generate HTML documentation.

- `make docs` - Generate HTML documentation and serve it to the browser.

- `make pre-release increment={major/minor/patch}` - Bump the version and create a release tag. Should only be run from the _main_ branch. Passes the increment value to bump2version to create a new version number dynamically. The new version number will be added to _\_\_version\_\_.py_ and _pyproject.toml_ and a new commit will be logged. The tag will be created from the new commit.
