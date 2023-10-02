# Developer Setup

To begin local development, clone the [litestar-org/litestar-fullstack](https://github.com/litestar-org/litestar-fullstack) repository and use one of the following methods to build it. Commands should be executed from inside of the project home folder.

## Using PDM

```bash
pdm install
```

Install optional dependencies using the `--G` flag:

```bash
pdm install --G:all
```

## Using pip

```bash
pip install .
```

Install optional dependencies using square brackets:

```bash
pip install .[dev,docs,lint]
```

## Using a local docker build

To build an image locally from the Dockerfile:

To build an image ready for production deployment run:

```bash
docker compose -f docker-compose.yml build
```

To build an development image, run:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml build
```

To run the image:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
docker compose run app manage create-database
```
