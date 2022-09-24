import multiprocessing
import platform
from typing import Any

import click

from app.cli import commands
from app.config import log_config, settings


@click.group(help=settings.app.NAME)
def cli(**options: dict[str, Any]) -> None:
    log_config.configure()
    if platform.system() == "Darwin":
        multiprocessing.set_start_method("fork", force=True)


cli.add_command(commands.run.cli, name="run")
cli.add_command(commands.manage.cli, name="manage")


if __name__ == "__main__":
    cli()
