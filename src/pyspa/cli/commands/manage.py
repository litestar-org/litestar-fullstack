import typer

from pyspa.cli.console import console
from pyspa.config.logging import get_logger

logger = get_logger("pyspa")

cli = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="markdown",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    add_completion=False,
)


@cli.command()
def pull_secret(secret_name: str) -> None:
    """Pull Secrets from Secrets Provider"""
    console.print("[bold green]...Gathering data")
    logger.info("[bold red]...Gathering data")


@cli.command()
def push_secret(secret_name: str) -> None:
    """Pull Secrets from Secrets Provider"""
    console.print("[bold green]...Gathering data")


@cli.command()
def bundle_scripts() -> None:
    """Push secrets to Secrets Provider"""
    console.print("[bold blue]...exporting shell scripts")
