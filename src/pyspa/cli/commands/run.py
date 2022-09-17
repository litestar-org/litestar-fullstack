import typer
import uvicorn

from pyspa.cli.console import console
from pyspa.config import settings
from pyspa.config.logging import log_config

cli = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="markdown",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    add_completion=False,
)


@cli.command(name="server")
def server(
    host: str = typer.Option(
        settings.server.HOST,
        "--host",
        "-h",
        help="Host interface to listen on.  Use 0.0.0.0 for all available interfaces.",
    ),
    port: int = typer.Option(settings.server.PORT, "--port", "-p", help="Port to listen on."),
    workers: int = typer.Option(
        settings.server.HTTP_WORKERS,
        "--workers",
        "-w",
        help="Number of HTTP workers to run.",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Reload the application on code changes",
    ),
) -> None:
    """Run the API server."""
    log_config.configure()
    console.print("[bold blue]Launching API Server with Uvicorn")
    settings.server.HOST = host
    settings.server.PORT = port
    settings.server.HTTP_WORKERS = workers
    settings.server.RELOAD = reload

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
