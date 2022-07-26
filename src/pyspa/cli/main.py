import typer

from pyspa.cli.commands import admin_cli, run_cli

cli = typer.Typer(name="Simple Single Page Application", no_args_is_help=True)

cli.add_typer(run_cli, name="run")
cli.add_typer(admin_cli, name="admin")
