import binascii
import multiprocessing
import os
import platform
import sys
from typing import Any

import rich_click as click
import uvicorn
from click import echo
from rich import get_console
from rich.prompt import Confirm
from starlite_saqlalchemy.constants import IS_LOCAL_ENVIRONMENT

from app.lib import db, log, settings, worker

__all__ = ["app"]


click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = ""
click.rich_click.MAX_WIDTH = 80
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
console = get_console()
"""Pre-configured CLI Console."""

logger = log.getLogger()


@click.group(help="Starlite Reference Application")
def app(**_: dict[str, "Any"]) -> None:
    """CLI application entrypoint."""
    log.config.configure()
    if platform.system() == "Darwin":
        multiprocessing.set_start_method("fork", force=True)


# API App
#
#
#


@click.group(name="run", invoke_without_command=False, help="Run application services.")
@click.pass_context
def run_app(_: dict[str, Any]) -> None:
    """Launch Application Components."""


@run_app.command(name="server", help="Starts the application server")
@click.option(
    "--host",
    help="Host interface to listen on.  Use 0.0.0.0 for all available interfaces.",
    type=click.STRING,
    default=settings.server.HOST,
    required=False,
    show_default=True,
)
@click.option(
    "-p",
    "--port",
    help="Port to bind.",
    type=click.INT,
    default=settings.server.PORT,
    required=False,
    show_default=True,
)
@click.option(
    "--http-workers",
    help="The number of HTTP worker processes for handling requests.",
    type=click.IntRange(min=1, max=multiprocessing.cpu_count() + 1),
    default=multiprocessing.cpu_count() + 1,
    required=False,
    show_default=True,
)
@click.option(
    "--worker-concurrency",
    help="The number of simultaneous jobs a worker process can execute.",
    type=click.IntRange(min=1),
    default=settings.worker.CONCURRENCY,
    required=False,
    show_default=True,
)
@click.option("-r", "--reload", help="Enable reload", is_flag=True, default=False, type=bool)
@click.option("-v", "--verbose", help="Enable verbose logging.", is_flag=True, default=False, type=bool)
@click.option("-d", "--debug", help="Enable debugging.", is_flag=True, default=False, type=bool)
def run_server(  # noqa: PLR0913
    host: str,
    port: int | None,
    http_workers: int | None,
    worker_concurrency: int | None,
    reload: bool | None,
    verbose: bool | None,
    debug: bool | None,
) -> None:
    """Run the API server."""
    log.config.configure()
    settings.server.HOST = host or settings.server.HOST
    settings.server.PORT = port or settings.server.PORT
    settings.server.RELOAD = (
        reload or settings.server.RELOAD if settings.server.RELOAD is not None else IS_LOCAL_ENVIRONMENT
    )
    settings.server.HTTP_WORKERS = http_workers or settings.server.HTTP_WORKERS
    settings.worker.CONCURRENCY = worker_concurrency or settings.worker.CONCURRENCY
    settings.app.DEBUG = debug or settings.app.DEBUG
    settings.log.LEVEL = 10 if verbose or settings.app.DEBUG else settings.log.LEVEL
    logger.info("starting application.")
    try:
        logger.info("starting Background worker processes.")
        worker_process = multiprocessing.Process(target=worker.run_worker)
        worker_process.start()
        logger.info("Starting HTTP Server.")

        uvicorn.run(
            app=settings.server.APP_LOC,
            factory=settings.server.APP_LOC_IS_FACTORY,
            host=settings.server.HOST,
            port=settings.server.PORT,
            loop="uvloop",
            reload=bool(settings.server.RELOAD),
            reload_dirs=settings.server.RELOAD_DIRS if settings.server.RELOAD else None,
            timeout_keep_alive=settings.server.KEEPALIVE,
            log_config=None,
            # access_log=False,
            lifespan="off",
            workers=1 if bool(settings.server.RELOAD) else settings.server.HTTP_WORKERS,
        )
    except Exception as e:
        logger.error(e)

    finally:
        if worker_process.is_alive():
            worker_process.kill()
        logger.info("⏏️  Shutdown complete")
        sys.exit()


@click.option(
    "--worker-concurrency",
    help="The number of simultaneous jobs a worker process can execute.",
    type=click.IntRange(min=1),
    default=settings.worker.CONCURRENCY,
    required=False,
    show_default=True,
)
@click.option("-v", "--verbose", help="Enable verbose logging.", is_flag=True, default=False, type=bool)
@click.option("-d", "--debug", help="Enable debugging.", is_flag=True, default=False, type=bool)
def run_worker(
    worker_concurrency: int | None,
    verbose: bool | None,
    debug: bool | None,
) -> None:
    """Run the API server."""
    log.config.configure()
    settings.worker.CONCURRENCY = worker_concurrency or settings.worker.CONCURRENCY
    settings.app.DEBUG = debug or settings.app.DEBUG
    settings.log.LEVEL = 10 if verbose or settings.app.DEBUG else settings.log.LEVEL
    logger.info("starting Background worker processes.")
    worker.run_worker()


@click.group(name="manage", invoke_without_command=False, help="Application Management Commands")
@click.pass_context
def management_app(_: dict[str, Any]) -> None:
    """System Administration Commands."""


@management_app.command(name="generate-random-key")
@click.option(
    "--length",
    "-l",
    help="Length of random key to generate",
    type=click.INT,
    default=32,
    required=False,
    show_default=False,
)
def generate_random_key(length: int) -> None:
    """Admin helper to generate random character string."""
    console.print(f"KEY: {binascii.hexlify(os.urandom(length)).decode()}")


@management_app.command(
    name="create-database",
    help="Creates an empty postgres database and executes migrations",
)
def create_database() -> None:
    """Create database DDL migrations."""
    db.utils.create_database()


@management_app.command(
    name="upgrade-database",
    help="Executes migrations to apply any outstanding database structures.",
)
def upgrade_database() -> None:
    """Upgrade the database to the latest revision."""
    db.utils.upgrade_database()


@management_app.command(
    name="reset-database",
    help="Executes migrations to apply any outstanding database structures.",
)
@click.option(
    "--no-prompt",
    help="Do not prompt for confirmation.",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=True,
    is_flag=True,
)
def reset_database(no_prompt: bool) -> None:
    """Reset the database to an initial empty state."""
    if not no_prompt:
        Confirm.ask("Are you sure you want to drop and recreate everything?")
    db.utils.reset_database()


@management_app.command(
    name="purge-database",
    help="Drops all tables.",
)
@click.option(
    "--no-prompt",
    help="Do not prompt for confirmation.",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=True,
    is_flag=True,
)
def purge_database(no_prompt: bool) -> None:
    """Drop all objects in the database."""
    if not no_prompt:
        confirmed = Confirm.ask(
            "Are you sure you want to drop everything?",
        )
        if not confirmed:
            echo("Aborting database purge and exiting.")
            sys.exit(0)
    db.utils.purge_database()


@management_app.command(
    name="show-current-database-revision",
    help="Shows the current revision for the database.",
)
def show_database_revision() -> None:
    """Show current database revision."""
    db.utils.show_database_revision()


app.add_command(management_app, name="manage")
app.add_command(run_app, name="run")
