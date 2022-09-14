import typer

from pyspa.asgi import run_server
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


@cli.command()
def api(
    host: str = typer.Option(
        settings.server.HOST,
        "--host",
        "-h",
        help="Host interface to listen on.  Use 0.0.0.0 for all available interfaces.",
    ),
    port: int = typer.Option(settings.server.PORT, "--port", "-p", help="Port to listen on."),
    workers: int = typer.Option(
        settings.server.WORKERS,
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
    settings.server.WORKERS = workers
    settings.server.RELOAD = reload
    run_server(
        host=settings.server.HOST,
        port=settings.server.PORT,
        http_workers=settings.server.WORKERS,
        reload=settings.server.RELOAD,
        log_level=settings.server.LOG_LEVEL,
        asgi_app=settings.server.ASGI_APP,
    )
