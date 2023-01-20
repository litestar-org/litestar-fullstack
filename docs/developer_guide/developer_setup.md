# Developer Setup

To begin local development, clone the [cofin/typer_cli/starlite-full-stack-example](https://github.com/cofin/starlite-full-stack-example) repository and use one of the following methods to build it. Commands should be executed from inside of the project home folder.

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

## Using a local docker build

To build an image locally from the Dockerfile:

```bash
make build
```

To run the image:

```bash
docker run --rm app hello user
docker run --rm app goodbye user
docker run --rm app version
```
