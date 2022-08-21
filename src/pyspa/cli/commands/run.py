import typer

from pyspa.cli.console import console
from pyspa.config import settings
from pyspa.config.logging import get_logger
from pyspa.core.wsgi import run_wsgi

cli = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="markdown",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    add_completion=False,
)

logger = get_logger("root")


@cli.command(name="server")
def run_server(
    host: str = typer.Option(
        settings.gunicorn.HOST,
        help="Host interface to listen on.  Use 0.0.0.0 for all available interfaces.",
    ),
    port: int = typer.Option(settings.gunicorn.PORT, help="Port to listen on."),
    workers: int = typer.Option(
        settings.gunicorn.WORKERS,
        help="Number of HTTP workers to run.  This should equal the number of CPUs available.",
    ),
) -> None:
    """Run the server"""
    settings.gunicorn.HOST = host
    settings.gunicorn.PORT = port
    settings.gunicorn.WORKERS = workers
    console.print("[bold green]...Gathering data")
    run_wsgi(host, port, workers, reload=settings.gunicorn.RELOAD)


@cli.command(name="worker")
def run_worker() -> None:
    """Run the worker"""
    console.print("[bold green]...Gathering data")
    logger.info("Running worker")
