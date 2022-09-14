import typer

from pyspa.cli import commands

cli = typer.Typer(
    name="Simple Single Page Application",
    no_args_is_help=True,
    rich_markup_mode="markdown",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    add_completion=False,
)
cli.add_typer(
    commands.run.cli,
    name="run",
    help="Launch Starlite PySPA",
)
cli.add_typer(
    commands.manage.cli,
    name="manage",
    help="Configure Starlite PySPA",
)
