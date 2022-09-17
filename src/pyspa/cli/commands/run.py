import multiprocessing
import os
from typing import Any, Dict

import click

from pyspa.cli.console import console, print_prologue
from pyspa.config import settings
from pyspa.config.logging import log_config


@click.group(name="run", invoke_without_command=False)
@click.pass_context
def cli(_: Dict[str, Any]) -> None:
    """Run Commands"""


@cli.command(name="server", help="Starts the application server")
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
    help="The number of worker processes for handling requests.",
    type=click.IntRange(min=1, max=multiprocessing.cpu_count()),
    default=2,
    required=False,
    show_default=True,
)
@click.option("-r", "--reload", help="Enable reload", is_flag=True, default=False, type=click.BOOL)
@click.option("-v", "--verbose", help="Enable verbose logging.", is_flag=True, default=False, type=click.BOOL)
def run_server(host: str, port: int, http_workers: int, reload: bool, verbose: bool) -> None:
    """Run the API server."""
    log_config.configure()
    print_prologue(
        is_interactive=console.is_interactive,
        custom_header=_generate_header_info(),
    )
    settings.server.HOST = host
    settings.server.PORT = port
    settings.server.HTTP_WORKERS = http_workers
    settings.server.RELOAD = reload
    settings.app.LOG_LEVEL = "DEBUG" if bool(verbose) else "INFO"
    import uvicorn

    uvicorn.run(
        app=settings.server.ASGI_APP,
        host=settings.server.HOST,
        port=settings.server.PORT,
        log_level=settings.server.UVICORN_LOG_LEVEL.lower(),
        log_config=None,  # this tells uvicorn to not apply its customizations
        reload=settings.server.RELOAD,
        lifespan="auto",
        access_log=True,
        workers=settings.server.HTTP_WORKERS,
        reload_excludes=[".git", ".venv", "*.pyc"],
    )


def _generate_header_info(title: str = "Starlite Application") -> str:
    """Generates the header info

    Args:
        base_params (dict): The base params
    Returns:
        str: The header info
    """
    return f"""
    [bold blue]{title}[/bold blue]
    Listening at: {settings.server.HOST}
    Number of http workers: {settings.server.HTTP_WORKERS}
    Number of background workers: {settings.server.BACKGROUND_WORKERS}
    Host CPU: {multiprocessing.cpu_count()} cores
    Host Memory: {round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 / 1024)} MB
    """
