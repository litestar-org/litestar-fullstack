<p align="center">
  <a href="https://user-images.githubusercontent.com/20674972/178172752-abd4497d-6a0e-416b-9eef-1b1c0dca8477.png">
    <img src="https://user-images.githubusercontent.com/20674972/178172752-abd4497d-6a0e-416b-9eef-1b1c0dca8477.png" alt="Pytemplates Banner" style="width:100%;">
  </a>
</p>

### A production ready python CLI template

- Metadata and dependency information is stored in the pyproject.toml for compatibility with both [pip](https://pip.pypa.io/en/stable/) and [poetry](https://python-poetry.org/docs/).
- [Flake8](https://flake8.pycqa.org/en/latest/), [pylint](https://pylint.pycqa.org/en/latest/index.html), and [isort](https://pycqa.github.io/isort/) configurations are defined to be compatible with the [black](https://black.readthedocs.io/en/stable/) autoformatter.
- Pylint settings are based on the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) and adapted for black compatibility.
- Linting tools run automatically before each commit using [pre-commit](https://pre-commit.com/), black, and isort.
- Test coverage reports are generated during every commit and pull request using [coverage](https://coverage.readthedocs.io/en/6.4.1/) and [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/). All reports are automatically uploaded and archived on [codecov.io](https://about.codecov.io/).
- Unit tests are written using [pytest](https://docs.pytest.org/en/latest/) and static type checking is provided by [mypy](http://mypy-lang.org/index.html).
- Package releases to [PyPI](https://pypi.org/) with dynamic versioning provided by [bump2version](https://github.com/c4urself/bump2version) begin automatically whenever a new tag is created in github.
- Docker images are automatically published to [Docker Hub](https://hub.docker.com/) during every release. Images are tagged with a semantic version number which agrees with the git tag and the PyPI version number.
- Documentation is built using [mkdocs](https://www.mkdocs.org/) and [mkdocstrings](https://mkdocstrings.github.io/). Docs are automatically deployed to [github pages](https://docs.github.com/en/pages) during every release.
- Release notes are automatically generated during every release using [github actions](https://docs.github.com/en/actions).
