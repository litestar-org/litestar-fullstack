import binascii
import multiprocessing
import os
import platform
import subprocess
import sys
from json import dumps
from pathlib import Path
from typing import Any

import anyio
import rich_click as click
from click import Path as ClickPath
from click import echo
from jsbeautifier import Beautifier
from pydantic import EmailStr, SecretStr
from rich import get_console
from rich.prompt import Confirm
from starlite._openapi.typescript_converter.converter import (
    convert_openapi_to_typescript,
)
from starlite.cli._utils import StarliteCLIException
from yaml import dump as dump_yaml

from app.asgi import create_app
from app.domain.accounts.schemas import UserCreate, UserUpdate
from app.domain.accounts.services import UserService
from app.domain.web.vite import run_vite
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

logger = log.get_logger()


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
def run_server(
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
    settings.server.RELOAD = reload or settings.server.RELOAD if settings.server.RELOAD is not None else None
    settings.server.HTTP_WORKERS = http_workers or settings.server.HTTP_WORKERS
    settings.worker.CONCURRENCY = worker_concurrency or settings.worker.CONCURRENCY
    settings.app.DEBUG = debug or settings.app.DEBUG
    settings.log.LEVEL = 10 if verbose or settings.app.DEBUG else settings.log.LEVEL
    logger.info("starting all application services.")

    try:
        logger.info("starting Background worker processes.")
        worker_process = multiprocessing.Process(target=worker.run_worker)
        worker_process.start()

        if settings.app.DEV_MODE:
            logger.info("starting Vite")
            vite_process = multiprocessing.Process(target=run_vite)
            vite_process.start()

        logger.info("Starting HTTP Server.")
        reload_dirs = settings.server.RELOAD_DIRS if settings.server.RELOAD else None
        process_args = {
            "reload": bool(settings.server.RELOAD),
            "host": settings.server.HOST,
            "port": settings.server.PORT,
            "workers": 1 if bool(settings.server.RELOAD or settings.app.DEV_MODE) else settings.server.HTTP_WORKERS,
            "factory": settings.server.APP_LOC_IS_FACTORY,
            "loop": "uvloop",
            "no-access-log": True,
            "timeout-keep-alive": settings.server.KEEPALIVE,
        }
        if reload_dirs:
            process_args.update({"reload-dir": reload_dirs})
        subprocess.run(["uvicorn", settings.server.APP_LOC, *_convert_uvicorn_args(process_args)], check=True)

    finally:
        if worker_process.is_alive():
            worker_process.kill()
        if vite_process.is_alive():
            vite_process.kill()
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


@management_app.command(name="create-user", help="Create a user")
@click.option(
    "--email",
    help="Email of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--name",
    help="Full name of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--password",
    help="Password",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--superuser",
    help="Is a superuser",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=False,
    is_flag=True,
)
def create_user(
    email: str | None,
    name: str | None,
    password: str | None,
    superuser: bool | None,
) -> None:
    """Create a user."""

    async def _create_user(
        email: str,
        name: str,
        password: str,
        superuser: bool = False,
    ) -> None:
        obj_in = UserCreate(
            email=EmailStr(email),
            name=name,
            password=SecretStr(password),
            is_superuser=superuser,
        )

        async with UserService.new() as users_service:
            user = await users_service.create(data=obj_in.dict(exclude_unset=True, exclude_none=True))
            await users_service.repository.session.commit()
            logger.info("User created: %s", user.email)

    email = email or click.prompt("Email")
    name = name or click.prompt("Full Name", show_default=False)
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    superuser = superuser or click.prompt("Create as superuser?", show_default=True, type=click.BOOL)

    anyio.run(_create_user, email, name, password, superuser)


@management_app.command(name="promote-to-superuser", help="Promotes a user to application superuser")
@click.option(
    "--email",
    help="Email of the user",
    type=click.STRING,
    required=False,
    show_default=False,
)
def promote_to_superuser(email: EmailStr) -> None:
    """Promote to Superuser.

    Args:
        email (EmailStr): _description_
    """

    async def _promote_to_superuser(email: EmailStr) -> None:
        async with UserService.new() as users_service:
            user = await users_service.get_one_or_none(email=email)
            if user:
                logger.info("Promoting user: %s", user.email)
                user_in = UserUpdate(
                    email=EmailStr(user.email),
                    is_superuser=True,
                )
                user = await users_service.update(
                    item_id=user.id,
                    data=user_in.dict(exclude_unset=True, exclude_none=True),
                )
                await users_service.repository.session.commit()
                logger.info("Upgraded %s to superuser", email)
            else:
                logger.warning("User not found: %s", email)

    anyio.run(_promote_to_superuser, email)


@management_app.command("export-openapi")
@click.option(
    "--output",
    help="Path to export the openapi schema.",
    type=ClickPath(dir_okay=False, path_type=Path),  # type: ignore[type-var]
    default=Path("openapi_schema.json"),
    show_default=True,
)
def generate_openapi_schema(output: Path) -> None:
    """Generate an OpenAPI Schema."""
    app = create_app()
    if not app.openapi_schema:  # pragma: no cover
        raise StarliteCLIException("Starlite application does not have an OpenAPI schema")

    if output.suffix in (".yml", ".yaml"):
        content = dump_yaml(app.openapi_schema.to_schema(), default_flow_style=False)
    else:
        content = dumps(app.openapi_schema.to_schema(), indent=4)

    try:
        output.write_text(content)
    except OSError as e:  # pragma: no cover
        raise StarliteCLIException(f"failed to write schema to path {output}") from e


beautifier = Beautifier()


@management_app.command("export-typescript-types")
@click.option(
    "--output",
    help="output file path",
    type=ClickPath(dir_okay=False, path_type=Path),  # type: ignore[type-var]
    default=Path("api-specs.d.ts"),
    show_default=True,
)
@click.option("--namespace", help="namespace to use for the typescript specs", type=str, default="API")
def generate_typescript_specs(output: Path, namespace: str) -> None:
    """Generate TypeScript specs from the OpenAPI schema."""
    app = create_app()
    if not app.openapi_schema:  # pragma: no cover
        raise StarliteCLIException("Starlite application does not have an OpenAPI schema")

    try:
        specs = convert_openapi_to_typescript(app.openapi_schema, namespace)
        beautified_output = beautifier.beautify(specs.write())
        output.write_text(beautified_output)
    except OSError as e:  # pragma: no cover
        raise StarliteCLIException(f"failed to write schema to path {output}") from e


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


def _convert_uvicorn_args(args: dict[str, Any]) -> list[str]:
    process_args = []
    for arg, value in args.items():
        if value is None:
            pass
        if isinstance(value, list):
            for val in value:
                if val is None:
                    pass
                process_args.append(f"--{arg}={val}")
        if isinstance(value, bool):
            if value:
                process_args.append(f"--{arg}")
        else:
            process_args.append(f"--{arg}={value}")

    return process_args
