import typer

from pyspa.cli.console import console
from pyspa.config.logging import get_logger

cli = typer.Typer(no_args_is_help=True)

logger = get_logger("root")


@cli.command(name="server")
def run_server(
    host: str,
) -> None:
    """Run the server"""
    console.print("[bold green]...Gathering data")
    logger.error("[bold red]Running server")


@cli.command(name="worker")
def run_worker() -> None:
    """Run the worker"""
    console.print("[bold green]...Gathering data")
    logger.info("Running worker")
