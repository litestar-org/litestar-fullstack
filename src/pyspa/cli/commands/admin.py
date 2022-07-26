import typer

from pyspa.cli.console import console

cli = typer.Typer(no_args_is_help=True)


@cli.command()
def pull_secret(secret_name: str) -> None:
    """Pull Secrets from Secrets Provider"""
    console.print("[bold green]...Gathering data")


@cli.command()
def push_secret(secret_name: str) -> None:
    """Pull Secrets from Secrets Provider"""
    console.print("[bold green]...Gathering data")


@cli.command()
def bundle_scripts() -> None:
    """Push secrets to Secrets Provider"""
    console.print("[bold blue]...exporting shell scripts")
