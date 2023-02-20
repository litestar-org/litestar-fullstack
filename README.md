# starlite-plugin-example

## quick start commands

### install development environment

```bash
make install
```

### edit env file

```bash
cp env.example .env
```

Edit `SECRET_KEY`, `DATABASE_URI`, and `REDIS_URL`

You can generate a SECRET_KET by running:
`poetry run app manage generate-random-key`

### deploy migrations

You can run most of the database commands with the integrated CLI tool.

To deploy migration to the database, execute:
`poetry run app manage upgrade-database`

### start the server in DEBUG mode (development mode)

if DEBUG is set to true, the base template expects that Vite will be running. You'll need to open 2 terminal shells at the moment to get the environment running.

in terminal one, run `npm run dev`.

in the second terminal, run `poetry run app run api --reload`

### start the server in production mode

if DEBUG is false, the server will look for the static assets that are produced from the `npm run build` command. Please be sure to have run this before starting th server.

```bash
npm run build # generates static assets from vite and puts them `src/app/domain/web/public`
poetry run app run api
```

## App Commands

```bash
❯ poetry run app

 Usage: app [OPTIONS] COMMAND [ARGS]...

 Starlite Reference Application

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
│ generate-random-key             Admin helper to generate random character    │
│                                 string.                                      │
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
