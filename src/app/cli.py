import multiprocessing
import subprocess
import sys
from typing import Any

import anyio
import click
from anyio import open_process
from anyio.streams.text import TextReceiveStream
from pydantic import EmailStr
from rich import get_console

from app.domain import plugins
from app.domain.accounts.dtos import UserCreate, UserUpdate
from app.domain.accounts.services import UserService
from app.lib import log, settings, worker

__all__ = [
    "create_database",
    "create_user",
    "run_all_app",
    "run_app",
    "run_worker",
    "user_management_app",
    "worker_management_app",
]


console = get_console()
"""Pre-configured CLI Console."""

logger = log.get_logger()


@click.group(name="serve", invoke_without_command=False, help="Run application services.")
@click.pass_context
def run_app(_: dict[str, Any]) -> None:
    """Launch Application Components."""


@click.group(name="database", invoke_without_command=False, help="Manage the configured database backend.")
@click.pass_context
def database_management_app(_: dict[str, Any]) -> None:
    """Manage the configured database backend."""


@click.group(name="users", invoke_without_command=False, help="Manage application users.")
@click.pass_context
def user_management_app(_: dict[str, Any]) -> None:
    """Manage application users."""


@click.group(name="worker", invoke_without_command=False, help="Manage application background workers.")
@click.pass_context
def worker_management_app(_: dict[str, Any]) -> None:
    """Manage application users."""


@click.group(
    name="run-all",
    invoke_without_command=True,
    help="Starts the application server & worker in a single command.",
)
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
def run_all_app(
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
            "loop": "auto",
            "no-access-log": True,
            "timeout-keep-alive": settings.server.KEEPALIVE,
        }
        if reload_dirs:
            process_args["reload-dir"] = reload_dirs
        subprocess.run(
            ["uvicorn", settings.server.APP_LOC, *_convert_uvicorn_args(process_args)],  # noqa: S607
            check=True,
        )
    finally:
        for process in multiprocessing.active_children():
            process.terminate()
        logger.info("⏏️  Shutdown complete")
        sys.exit()


@worker_management_app.command(name="run", help="Starts the background workers.")
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


@user_management_app.command(name="create-user", help="Create a user")
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
            password=password,
            is_superuser=superuser,
        )

        async with UserService.new() as users_service:
            user = await users_service.create(data=obj_in.__dict__)
            await users_service.repository.session.commit()
            logger.info("User created: %s", user.email)

    email = email or click.prompt("Email")
    name = name or click.prompt("Full Name", show_default=False)
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    superuser = superuser or click.prompt("Create as superuser?", show_default=True, type=click.BOOL)

    anyio.run(_create_user, email, name, password, superuser)


@user_management_app.command(name="promote-to-superuser", help="Promotes a user to application superuser")
@click.option(
    "--email",
    help="Email of the user",
    type=click.STRING,
    required=False,
    show_default=False,
)
def promote_to_superuser(email: str) -> None:
    """Promote to Superuser.

    Args:
        email (str): _description_
    """

    async def _promote_to_superuser(email: str) -> None:
        async with UserService.new() as users_service:
            user = await users_service.get_one_or_none(email=email)
            if user:
                logger.info("Promoting user: %s", user.email)
                user_in = UserUpdate(
                    email=user.email,
                    is_superuser=True,
                )
                user = await users_service.update(
                    item_id=user.id,
                    data=user_in.__dict__,
                )
                await users_service.repository.session.commit()
                logger.info("Upgraded %s to superuser", email)
            else:
                logger.warning("User not found: %s", email)

    anyio.run(_promote_to_superuser, email)



def _convert_uvicorn_args(args: dict[str, Any]) -> list[str]:
    process_args = []
    for arg, value in args.items():
        if isinstance(value, list):
            process_args.extend(f"--{arg}={val}" for val in value)
        if isinstance(value, bool):
            if value:
                process_args.append(f"--{arg}")
        else:
            process_args.append(f"--{arg}={value}")

    return process_args


def run_vite() -> None:
    """Run Vite in a subprocess."""
    try:
        anyio.run(_run_vite, backend="asyncio", backend_options={"use_uvloop": True})
    except KeyboardInterrupt:
        logger.info("Stopping typescript development services.")
    finally:
        logger.info("Vite Service stopped.")


async def _run_vite() -> None:
    """Run Vite in a subprocess."""
    log.config.configure()
    async with await open_process(plugins.vite._config.run_command) as vite_process:
        async for text in TextReceiveStream(vite_process.stdout):  # type: ignore[arg-type]
            await logger.ainfo("Vite", message=text.replace("\n", ""))
