import typer

from pyspa.cli.commands import manage_cli, run_cli

cli = typer.Typer(
    name="Simple Single Page Application",
    no_args_is_help=True,
    rich_markup_mode="markdown",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    add_completion=False,
)

cli.add_typer(run_cli, name="run")
cli.add_typer(manage_cli, name="manage")
