# Litestar Reference Application

\*\* Update: This repo is referencing the current alpha of Litestar 2.0. Expect things to stabilize as we get closer to a final release.

This is a reference application that you can use to get your next Litestar application running quickly.

It contains most of the boilerplate required for a production web API.

Features:

- Latest Litestar configured with best practices
- Integration with SQLAlchemy 2.0, SAQ (Simple Asynchronous Queue), and litestar-saqlalchemy
- Extends built-in litestar click CLI
- Frontend integrated with vitejs and includes Jinja2 templates that integrate with Vite websocket/HMR support
- Multi-stage docker build using a Google Distroless (distroless/cc) Python 3.11 runtime image.
- pre-configured user model that includes teams and associated team roles
- examples of using guards for superuser and team based auth.

## App Commands

```bash
❯ poetry shell
Virtual environment already activated: .venv
❯ app

 Usage: app [OPTIONS] COMMAND [ARGS]...

 Litestar CLI.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --app        TEXT       Module path to a Litestar application (TEXT)                             │
│ --app-dir    DIRECTORY  Look for APP in the specified directory, by adding this to the           │
│                         PYTHONPATH. Defaults to the current working directory.                   │
│                         (DIRECTORY)                                                              │
│ --help                  Show this message and exit.                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ database      Manage the configured database backend.                                            │
│ info          Show information about the detected Litestar app.                                  │
│ routes        Display information about the application's routes.                                │
│ run           Run a Litestar app.                                                                │
│ run-all       Starts the application server & worker in a single command.                        │
│ schema        Manage server-side OpenAPI schemas.                                                │
│ sessions      Manage server-side sessions.                                                       │
│ users         Manage application users.                                                          │
│ version       Show the currently installed Litestar version.                                     │
│ worker        Manage application background workers.                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

```

## Database Commands

```bash
❯ app database

 Usage: app database [OPTIONS] COMMAND [ARGS]...

 Manage the configured database backend.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --help      Show this message and exit.                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ create-database                 Creates an empty postgres database and executes migrations       │
│ purge-database                  Drops all tables.                                                │
│ reset-database                  Executes migrations to apply any outstanding database            │
│                                 structures.                                                      │
│ show-current-database-revision  Shows the current revision for the database.                     │
│ upgrade-database                Executes migrations to apply any outstanding database            │
│                                 structures.                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

```

## Worker Commands

```bash
❯ app worker

 Usage: app worker [OPTIONS] COMMAND [ARGS]...

 Manage application background workers.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --help      Show this message and exit.                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ run         Starts the background workers.                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

```bash
❯ app run --help

 Usage: app run [OPTIONS]

 Run a Litestar app.
 The app can be either passed as a module path in the form of <module name>.<submodule>:<app
 instance or factory>, set as an environment variable LITESTAR_APP with the same format or
 automatically discovered from one of these canonical paths: app.py, asgi.py, application.py or
 app/__init__.py. When auto-discovering application factories, functions with the name
 ``create_app`` are considered, or functions that are annotated as returning a ``Litestar``
 instance.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --reload                    -r                             Reload server on changes              │
│ --port                      -p   INTEGER                   Serve under this port (INTEGER)       │
│                                                            [default: 8000]                       │
│ --web-concurrency           -wc  INTEGER RANGE [1<=x<=11]  The number of HTTP workers to launch  │
│                                                            (INTEGER RANGE)                       │
│                                                            [default: 1; 1<=x<=11]                │
│ --host                           TEXT                      Server under this host (TEXT)         │
│                                                            [default: 127.0.0.1]                  │
│ --fd,--file-descriptor           INTEGER                   Bind to a socket from this file       │
│                                                            descriptor.                           │
│                                                            (INTEGER)                             │
│ --uds,--unix-domain-socket       TEXT                      Bind to a UNIX domain socket. (TEXT)  │
│ --debug                                                    Run app in debug mode                 │
│ --pdb                                                      Drop into PDB on an exception         │
│ --reload-dir                     TEXT                      Directories to watch for file changes │
│                                                            (TEXT)                                │
│ --help                                                     Show this message and exit.           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

```

```bash
❯ app run-all --help

 Usage: app run-all [OPTIONS] COMMAND [ARGS]...

 Starts the application server & worker in a single command.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --host                    TEXT                      Host interface to listen on.  Use 0.0.0.0    │
│                                                     for all available interfaces.                │
│                                                     (TEXT)                                       │
│                                                     [default: 0.0.0.0]                           │
│ --port                -p  INTEGER                   Port to bind. (INTEGER) [default: 8000]      │
│ --http-workers            INTEGER RANGE [1<=x<=11]  The number of HTTP worker processes for      │
│                                                     handling requests.                           │
│                                                     (INTEGER RANGE)                              │
│                                                     [default: 11; 1<=x<=11]                      │
│ --worker-concurrency      INTEGER RANGE [x>=1]      The number of simultaneous jobs a worker     │
│                                                     process can execute.                         │
│                                                     (INTEGER RANGE)                              │
│                                                     [default: 1; x>=1]                           │
│ --reload              -r                            Enable reload                                │
│ --verbose             -v                            Enable verbose logging.                      │
│ --debug               -d                            Enable debugging.                            │
│ --help                                              Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Installation and Configuration

Commands to help you get this repository running.

### Install virtual environment and node packages

Most of the development related tasks are included in the `Makefile`. To install an environment with all development packages run:

```bash
make install
```

This command does the following:

- install `poetry` if it is not available in the path.
- create a virtual environment with all dependencies configured
- executes `npm ci` to install the node modules into the environment
- run `npm run build` to generate the static assets

### Edit .env configuration

There is a sample `.env` file located in the root of the repository.

```bash
cp env.example .env
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
❯ app database upgrade-database
2023-06-16T16:55:17.048183Z [info     ] Context impl PostgresqlImpl.
2023-06-16T16:55:17.048251Z [info     ] Will assume transactional DDL.
```

### Starting the server

#### Starting the server in development mode

if `DEV_MODE` is set to true, the base template expects that Vite will be running. When you start the application, it will try to start the vite service with the HMR websocket connection enabled.

```bash
❯ app run-all -p 8080
2023-06-16T16:58:38.049014Z [info     ] starting all application services.
2023-06-16T16:58:38.049058Z [info     ] starting Background worker processes.
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

if `DEV_MODE` is false, the server will look for the static assets that are produced from the `npm run build` command. Please be sure to have run this before starting th server.

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

- `make migrations`
- `make squash-migrations`
- `make upgrade`
