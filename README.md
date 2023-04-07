# Litestar Reference Application

\*\* Update: This repo is referencing the current alpha of Litestar 2.0. Expect things to stabilize as we get closer to a final release.

This is a reference application that you can use to get your next Litestar application running quickly.

It contains most of the boilerplate required for a production web API.

Features:

- Latest Litestar configured with best practices
- Integration with SQLAlchemy 2.0, SAQ (Simple Asynchronous Queue), and litestar-saqlalchemy
- Click based CLI that includes commands for database migrations and deployment
- Frontend integrated with vitejs and includes Jinja2 templates that integrate with Vite websocket/HMR support
- Multi-stage docker build using a Google Distroless (distroless/cc) Python 3.11 runtime image.
- pre-configured user model that includes teams and associated team roles
- examples of using guards for superuser and team based auth.

## App Commands

```bash
❯ poetry run app

 Usage: app [OPTIONS] COMMAND [ARGS]...

 Litestar Reference Application

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help    Show this message and exit.                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ manage         Application Management Commands                               │
│ run            Run application services.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯


```

## Management Commands

```bash
❯ poetry run app manage

 Usage: app manage [OPTIONS] COMMAND [ARGS]...

 Application Management Commands

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help    Show this message and exit.                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ create-database                 Creates an empty postgres database and       │
│                                 executes migrations                          │
│ create-user                     Create a user                                │
│ export-openapi                  Generate an OpenAPI Schema.                  │
│ export-typescript-types         Generate TypeScript specs from the OpenAPI   │
│                                 schema.                                      │
│ generate-random-key             Admin helper to generate random character    │
│                                 string.                                      │
│ promote-to-superuser            Promotes a user to application superuser     │
│ purge-database                  Drops all tables.                            │
│ reset-database                  Executes migrations to apply any outstanding │
│                                 database structures.                         │
│ show-current-database-revision  Shows the current revision for the database. │
│ upgrade-database                Executes migrations to apply any outstanding │
│                                 database structures.                         │
╰──────────────────────────────────────────────────────────────────────────────╯

```

## Run Commands

```bash
❯ poetry run app run

 Usage: app run [OPTIONS] COMMAND [ARGS]...

 Run application services.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help    Show this message and exit.                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ server          Starts the application server                                │
│ worker          Starts the background workers                                │
╰──────────────────────────────────────────────────────────────────────────────╯

```

```bash
❯ poetry run app run server --help

 Usage: app run server [OPTIONS]

 Starts the application server

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --host                    Host interface to listen on.  Use 0.0.0.0 for all  │
│                           available interfaces.                              │
│                           (TEXT)                                             │
│                           [default: 0.0.0.0]                                 │
│ --port                -p  Port to bind. (INTEGER) [default: 8000]            │
│ --http-workers            The number of HTTP worker processes for handling   │
│                           requests.                                          │
│                           (INTEGER RANGE)                                    │
│                           [default: 7; 1<=x<=7]                              │
│ --worker-concurrency      The number of simultaneous jobs a worker process   │
│                           can execute.                                       │
│                           (INTEGER RANGE)                                    │
│                           [default: 10; x>=1]                                │
│ --reload              -r  Enable reload                                      │
│ --verbose             -v  Enable verbose logging.                            │
│ --debug               -d  Enable debugging.                                  │
│ --help                    Show this message and exit.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

```bash
❯ poetry run app run worker --help

 Usage: app run worker [OPTIONS]

 Starts the background workers

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --worker-concurrency      The number of simultaneous jobs a worker process   │
│                           can execute.                                       │
│                           (INTEGER RANGE)                                    │
│                           [default: 1; x>=1]                                 │
│ --verbose             -v  Enable verbose logging.                            │
│ --debug               -d  Enable debugging.                                  │
│ --help                    Show this message and exit.                        │
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
❯ poetry run app manage generate-random-key
KEY: 5c5f2230767976c332b6f933b63b483a35148b2218e2cdfd0da992d859feae19
```

### Deploy Database Migrations

You can run most of the database commands with the integrated CLI tool.

To deploy migration to the database, execute:
`poetry run app manage upgrade-database`

### Starting the server

#### Starting the server in `DEBUG` mode (development mode)

if `DEBUG` is set to true, the base template expects that Vite will be running. You'll need to open 2 terminal shells at the moment to get the environment running.

in terminal one, run:

```bash
❯ npm run dev
> vite

Forced re-optimization of dependencies

  VITE v4.1.2  ready in 537 ms

  ➜  Local:   http://127.0.0.1:3000/static/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

in the second terminal, run:

```bash
❯ poetry run app run server --reload
2023-02-19 22:51:46 [info     ] starting application.
2023-02-19 22:51:46 [info     ] starting Background worker processes.
2023-02-19 22:51:46 [info     ] Starting HTTP Server.
```

#### start the server in production mode

if DEBUG is false, the server will look for the static assets that are produced from the `npm run build` command. Please be sure to have run this before starting th server.

```bash
npm run build # generates static assets from vite and
# files from the above command can be found in `src/app/domain/web/public`.
poetry run app run server
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
❯ poetry run app run server
2023-02-19 22:53:08 [info     ] starting application.
2023-02-19 22:53:08 [info     ] starting Background worker processes.
2023-02-19 22:53:08 [info     ] Starting HTTP Server.
^C2023-02-19 22:53:09 [info     ] ⏏️  Shutdown complete
```

## Make Commands

- `make migrations`
- `make squash-migrations`
- `make upgrade`
