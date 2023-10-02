<!-- markdownlint-disable -->
<p align="center">
  <img src="https://raw.githubusercontent.com/litestar-org/branding/1dc4635b192d29d864fcee6f3f73ea0ff6fecf10/assets/Branding%20-%20SVG%20-%20Transparent/Fullstack%20-%20Banner%20-%20Inline%20-%20Light.svg#gh-light-mode-only" alt="Litestar Logo - Light" width="100%" height="auto" />
  <img src="https://raw.githubusercontent.com/litestar-org/branding/1dc4635b192d29d864fcee6f3f73ea0ff6fecf10/assets/Branding%20-%20SVG%20-%20Transparent/Fullstack%20-%20Banner%20-%20Inline%20-%20Dark.svg#gh-dark-mode-only" alt="Litestar Logo - Dark" width="100%" height="auto" />
</p>
<!-- markdownlint-restore -->

<div align="center">
<!-- prettier-ignore-start -->

| Project   |     | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------- | :-- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CI/CD     |     | [![Tests and Linting](https://github.com/litestar-org/litestar-fullstack/actions/workflows/ci.yaml/badge.svg)](https://github.com/litestar-org/litestar-fullstack/actions/workflows/ci.yaml) [![Documentation Building](https://github.com/litestar-org/litestar-fullstack/actions/workflows/docs.yaml/badge.svg)](https://github.com/litestar-org/litestar-fullstack/actions/workflows/docs.yaml)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Quality   |     | [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=coverage)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar) [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar) [![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar) [![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar)                                                                                                                                                                                                                     |
| Community |     | [![Reddit](https://img.shields.io/reddit/subreddit-subscribers/litestarapi?label=r%2FLitestar&logo=reddit&labelColor=202235&color=edb641&logoColor=edb641)](https://reddit.com/r/litestarapi) [![Discord](https://img.shields.io/discord/919193495116337154?labelColor=202235&color=edb641&label=chat%20on%20discord&logo=discord&logoColor=edb641)](https://discord.gg/X3FJqy8d2j) [![Matrix](https://img.shields.io/badge/chat%20on%20Matrix-bridged-202235?labelColor=202235&color=edb641&logo=matrix&logoColor=edb641)](https://matrix.to/#/#litestar:matrix.org) [![Medium](https://img.shields.io/badge/Medium-202235?labelColor=202235&color=edb641&logo=medium&logoColor=edb641)](https://blog.litestar.dev) [![Twitter](https://img.shields.io/twitter/follow/LitestarAPI?labelColor=202235&color=edb641&logo=twitter&logoColor=edb641&style=flat)](https://twitter.com/LitestarAPI) [![Blog](https://img.shields.io/badge/Blog-litestar.dev-202235?logo=blogger&labelColor=202235&color=edb641&logoColor=edb641)](https://blog.litestar.dev)                                                                                                                                                                                              |
| Meta      |     | [![Litestar Project](https://img.shields.io/badge/Litestar%20Org-%E2%AD%90%20Litestar-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://github.com/litestar-org/litestar) [![types - Mypy](https://img.shields.io/badge/types-Mypy-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://github.com/python/mypy) [![License - MIT](https://img.shields.io/badge/license-MIT-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://spdx.org/licenses/) [![Litestar Sponsors](https://img.shields.io/badge/Sponsor-%E2%9D%A4-%23edb641.svg?&logo=github&logoColor=edb641&labelColor=202235)](https://github.com/sponsors/litestar-org) [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json&labelColor=202235)](https://github.com/astral-sh/ruff) [![code style - Black](https://img.shields.io/badge/code%20style-black-000000.svg?logo=python&labelColor=202235&logoColor=edb641)](https://github.com/psf/black) [![All Contributors](https://img.shields.io/github/all-contributors/litestar-org/litestar?labelColor=202235&color=edb641&logoColor=edb641)](#contributors-) |

<!-- prettier-ignore-end -->
</div>

# Litestar Fullstack Reference Application

This is a reference application that you can use to get your next Litestar application running quickly.

It contains most of the boilerplate required for a production web API with features like:

- Latest Litestar configured with best practices
- Integration with [SQLAlchemy 2.0](https://www.sqlalchemy.org/), [SAQ (Simple Asynchronous Queue)](https://saq-py.readthedocs.io/en/latest/), and [Structlog](https://www.structlog.org/en/stable/)
- Extends built-in Litestar click CLI
- Frontend integrated with ViteJS and includes Jinja2 templates that integrate with Vite websocket/HMR support
- Multi-stage Docker build using using a minimal Python 3.11 runtime image.
- Pre-configured user model that includes teams and associated team roles
- Examples of using guards for superuser and team-based auth.
- Examples using raw SQL for more complex queries

Take what you need and adapt it to your own projects

## Quick Start

To quickly get a development environment running, run the following:

```shell
make install
. .venv/bin/activate
```

## App Commands

```bash
❯ app

 Usage: app [OPTIONS] COMMAND [ARGS]...

 Litestar CLI.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --app          TEXT       Module path to a Litestar application (TEXT)       │
│ --app-dir      DIRECTORY  Look for APP in the specified directory, by adding │
│                           this to the PYTHONPATH. Defaults to the current    │
│                           working directory.                                 │
│                           (DIRECTORY)                                        │
│ --help     -h             Show this message and exit.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
Using Litestar app from env: 'app.asgi:create_app'
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ database   Manage SQLAlchemy database components.                            │
│ info       Show information about the detected Litestar app.                 │
│ routes     Display information about the application's routes.               │
│ run        Run a Litestar app.                                               │
│ run-all    Starts the application server & worker in a single command.       │
│ schema     Manage server-side OpenAPI schemas.                               │
│ sessions   Manage server-side sessions.                                      │
│ users      Manage application users.                                         │
│ version    Show the currently installed Litestar version.                    │
│ worker     Manage application background workers.                            │
╰──────────────────────────────────────────────────────────────────────────────╯

```

## Database Commands

```bash
❯ app database
Using Litestar app from env: 'app.asgi:create_app'

 Usage: app database [OPTIONS] COMMAND [ARGS]...

 Manage SQLAlchemy database components.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h    Show this message and exit.                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ downgrade              Downgrade database to a specific revision.            │
│ init                   Initialize migrations for the project.                │
│ make-migrations        Create a new migration revision.                      │
│ merge-migrations       Merge multiple revisions into a single new revision.  │
│ show-current-revision  Shows the current revision for the database.          │
│ stamp-migration        Mark (Stamp) a specific revision as current without   │
│                        applying the migrations.                              │
│ upgrade                Upgrade database to a specific revision.              │
╰──────────────────────────────────────────────────────────────────────────────╯

```

### Upgrading the Database

```bash
❯ app database upgrade
Using Litestar app from env: 'app.asgi:create_app'
Starting database upgrade process ───────────────────────────────────────────────
Are you sure you you want migrate the database to the "head" revision? [y/n]: y
2023-10-01T19:44:13.536101Z [debug    ] Using selector: EpollSelector
2023-10-01T19:44:13.623437Z [info     ] Context impl PostgresqlImpl.
2023-10-01T19:44:13.623617Z [info     ] Will assume transactional DDL.
2023-10-01T19:44:13.667920Z [info     ] Running upgrade  -> c3a9a11cc35d, init
2023-10-01T19:44:13.774932Z [debug    ] new branch insert c3a9a11cc35d
2023-10-01T19:44:13.783804Z [info     ] Pool disposed. Pool size: 5  Connections
 in pool: 0 Current Overflow: -5 Current Checked out connections: 0
2023-10-01T19:44:13.784013Z [info     ] Pool recreating
```

## Worker Commands

```bash
❯ app worker
Using Litestar app from env: 'app.asgi:create_app'

 Usage: app worker [OPTIONS] COMMAND [ARGS]...

 Manage application background workers.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h    Show this message and exit.                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ run       Starts the background workers.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯

```

## Run Commands

To run the application through Uvicorn using the standard Litestar CLI, you can use the following:

```bash
❯ app run --help
Using Litestar app from env: 'app.asgi:create_app'

 Usage: app run [OPTIONS]

 Run a Litestar app.
 The app can be either passed as a module path in the form of <module
 name>.<submodule>:<app instance or factory>, set as an environment variable
 LITESTAR_APP with the same format or automatically discovered from one of
 these canonical paths: app.py, asgi.py, application.py or app/__init__.py.
 When auto-discovering application factories, functions with the name
 ``create_app`` are considered, or functions that are annotated as returning a
 ``Litestar`` instance.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --reload                 -r                          Reload server on        │
│                                                      changes                 │
│ --reload-dir             -R  TEXT                    Directories to watch    │
│                                                      for file changes        │
│                                                      (TEXT)                  │
│ --port                   -p  INTEGER                 Serve under this port   │
│                                                      (INTEGER)               │
│                                                      [default: 8000]         │
│ --wc,--web-concurrency   -W  INTEGER RANGE           The number of HTTP      │
│                              [1<=x<=7]               workers to launch       │
│                                                      (INTEGER RANGE)         │
│                                                      [default: 1; 1<=x<=7]   │
│ --host                   -H  TEXT                    Server under this host  │
│                                                      (TEXT)                  │
│                                                      [default: 127.0.0.1]    │
│ --fd,--file-descriptor   -F  INTEGER                 Bind to a socket from   │
│                                                      this file descriptor.   │
│                                                      (INTEGER)               │
│ --uds,--unix-domain-so…  -U  TEXT                    Bind to a UNIX domain   │
│                                                      socket.                 │
│                                                      (TEXT)                  │
│ --debug                  -d                          Run app in debug mode   │
│ --pdb,--use-pdb          -P                          Drop into PDB on an     │
│                                                      exception               │
│ --help                   -h                          Show this message and   │
│                                                      exit.                   │
╰──────────────────────────────────────────────────────────────────────────────╯


```

The above command will not start the background workers. Those can be launched separately in another terminal.

Alternately, the `run-all` command will automatically start the background workers in separate processes.

```bash
❯ app run-all --help
Using Litestar app from env: 'app.asgi:create_app'

 Usage: app run-all [OPTIONS] COMMAND [ARGS]...

 Starts the application server & worker in a single command.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --host                    TEXT                     Host interface to listen  │
│                                                    on.  Use 0.0.0.0 for all  │
│                                                    available interfaces.     │
│                                                    (TEXT)                    │
│                                                    [default: 0.0.0.0]        │
│ --port                -p  INTEGER                  Port to bind.   (INTEGER) │
│                                                    [default: 8000]           │
│ --http-workers            INTEGER RANGE [1<=x<=7]  The number of HTTP worker │
│                                                    processes for handling    │
│                                                    requests.                 │
│                                                    (INTEGER RANGE)           │
│                                                    [default: 7; 1<=x<=7]     │
│ --worker-concurrency      INTEGER RANGE [x>=1]     The number of             │
│                                                    simultaneous jobs a       │
│                                                    worker process can        │
│                                                    execute.                  │
│                                                    (INTEGER RANGE)           │
│                                                    [default: 1; x>=1]        │
│ --reload              -r                           Enable reload             │
│ --verbose             -v                           Enable verbose logging.   │
│ --debug               -d                           Enable debugging.         │
│ --help                -h                           Show this message and     │
│                                                    exit.                     │
╰──────────────────────────────────────────────────────────────────────────────╯

```

## Installation and Configuration

Commands to help you get this repository running.

### Install virtual environment and node packages

Most of the development related tasks are included in the `Makefile`. To install an environment with all development packages run:

```bash
make install
```

This command does the following:

- install `pdm` if it is not available in the path.
- create a virtual environment with all dependencies configured
- build assets to be hosted by production asset server

### Edit .env configuration

There is a sample `.env` file located in the root of the repository.

```bash
cp .env.example .env
```

**Note** `SECRET_KEY`, `DATABASE_URI`, and `REDIS_URL` are the most important config settings. Be sure to set this properly.

You can generate a `SECRET_KEY` by running:

```bash
❯ openssl rand -base64 32

+U9UcN0meCsxkShMINkqZ7pcwpEpOC9AwOArZI6mYDU=
```

### Deploy Database Migrations

You can run most of the database commands with the integrated CLI tool.

To deploy migration to the database, execute:

```bash
❯ app database upgrade
2023-06-16T16:55:17.048183Z [info     ] Context impl PostgresqlImpl.
2023-06-16T16:55:17.048251Z [info     ] Will assume transactional DDL.
```

### Starting the server

#### Starting the server in development mode

if `DEV_MODE` is set to true, the base template expects that Vite will be running. When you start the application, it will try to start the vite service with the HMR websocket connection enabled.

```bash
❯ app run-all -p 8080
Using Litestar app from env: 'app.asgi:create_app'
2023-10-01T20:19:06.493377Z [info     ] starting all application services.
2023-10-01T20:19:06.493500Z [info     ] starting Background worker processes.
2023-06-16T16:58:38.055247Z [info     ] starting Vite
2023-06-16T16:58:38.056850Z [info     ] Starting HTTP Server.
2023-06-16T16:58:38.791943Z [info     ] Started server process [29108]
2023-06-16T16:58:38.792012Z [info     ] Waiting for application startup.
2023-06-16T16:58:38.794260Z [info     ] Application startup complete.
2023-06-16T16:58:38.794876Z [info     ] Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
2023-06-16T16:58:38.803751Z [info     ] Starting working pool
2023-06-16T16:58:38.804423Z [info     ] Worker is starting up.
2023-06-16T16:58:38.804519Z [info     ] Worker is starting up.
2023-06-16T16:58:38.816324Z [info     ] Performing background worker task.
2023-06-16T16:58:39.188218Z [info     ] Vite                           message=> litestar-fullstack@0.0.0 dev> vite
2023-06-16T16:58:39.894411Z [info     ] Vite                           message=Forced re-optimization of dependencies
2023-06-16T16:58:39.923813Z [info     ] Vite                           message=  VITE v4.3.9  ready in 676 ms
2023-06-16T16:58:39.924023Z [info     ] Vite                           message=  ➜  Local:   http://localhost:3000/static/  ➜  Network: use --host to expose
```

#### start the server in production mode

if `DEV_MODE` is false, the server will look for the static assets that are produced from the `npm run build` command. This command is automatically executed and the assets are bundled when running `pdm build`.

To manually rebuild assets, use the following:

```bash
npm run build # generates static assets from vite and
# files from the above command can be found in `src/app/domain/web/public`.
app run-all
```

Sample output:

```bash
❯ npm run build

> litestar-fullstack@0.0.0 build
> vue-tsc && vite build

vite v4.1.2 building for production...
✓ 15 modules transformed.
Generated an empty chunk: "vue".
../public/assets/vue-5532db34.svg    0.50 kB
../public/manifest.json              0.57 kB
../public/assets/main-b75adab1.css   1.30 kB │ gzip:  0.67 kB
../public/assets/vue-4ed993c7.js     0.00 kB │ gzip:  0.02 kB
../public/assets/main-17f9b70b.js    1.50 kB │ gzip:  0.80 kB
../public/assets/@vue-5be96905.js   52.40 kB │ gzip: 21.07 kB
❯ app run-all
2023-02-19 22:53:08 [info     ] starting application.
2023-02-19 22:53:08 [info     ] starting Background worker processes.
2023-02-19 22:53:08 [info     ] Starting HTTP Server.
```

## Make Commands

### Install Development Environment

This command will remove any existing environment and install a new environment with the latest dependencies.

```shell
make install
```

### Upgrade Project Dependencies

This command will upgrade all components of the application at the same time. It automatically executes:

- `pdm upgrade`
- `npm update`
- `pre-commit autoupdate`

```shell
make upgrade
```

### Execute Pre-commit

This command will automatically execute the pre-commit process for the project.

```shell
make lint
```

### Generate New Migrations

This command is a shorthand for executing `app database make-migrations`.

```shell
make migrations
```

### Upgrade a Database to the Latest Revision

This command is a shorthand for executing `app database upgrade`.

```shell
make migrate
```

### Execute Full Test Suite

This command executes all tests for the project.

```shell
make test
```
