import binascii
import logging
import os
import sys

import typer
from alembic import command as migration_command
from alembic.config import Config as AlembicConfig
from rich.prompt import Confirm
from sqlalchemy import Table
from sqlalchemy.schema import DropTable

from pyspa import utils
from pyspa.asgi import app
from pyspa.cli.console import console
from pyspa.config import settings
from pyspa.db import engine
from pyspa.models import BaseModel, meta

cli = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="markdown",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    add_completion=False,
)

logger = logging.getLogger()


@cli.command(name="generate-random-key")
def generate_random_key(length: int = 32) -> None:
    """Helper for admins to generate random 26 character string.

    Used as the secret key for sessions.
    Must be consistent (and secret) per environment.
    Output: b'random2323db3....1xyz'
    Copy the value in between the quotation marks to the settings file
    """
    console.print(binascii.hexlify(os.urandom(length)))


@cli.command(
    name="export-openapi-schema",
)
def export_api_schema(
    export_location: str = "domain/web/spec/openapi.json",
) -> None:
    """Push secrets to Secrets Provider"""

    console.print("Exporting API Schema")
    application = app
    schema = application.openapi_schema
    if schema:
        with open(export_location, "w", encoding="utf-8") as fd:
            fd.write(utils.serializers.serialize_object(application.openapi_schema))
        console.print_json(schema.json())


@cli.command(
    name="create-database",
    help="Creates an empty postgres database and executes migrations",
)
def create_database() -> None:
    """Create database DDL migrations."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    migration_command.upgrade(alembic_cfg, "head")


@cli.command(
    name="upgrade-database",
    help="Executes migrations to apply any outstanding database structures.",
)
def upgrade_database() -> None:
    """Upgrade the database to the latest revision."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    migration_command.upgrade(alembic_cfg, "head")


@cli.command(
    name="reset-database",
    help="Executes migrations to apply any outstanding database structures.",
)
def reset_database(
    no_prompt: bool = typer.Option(False, "--no-prompt", help="Do not prompt for confirmation"),
) -> None:
    """Resets the database to an initial empty state."""
    if not no_prompt:
        typer.confirm("[bold red] Are you sure you want to drop and recreate all tables?")
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)

    utils.asyncer.run(drop_tables)()

    console.log("Recreating the db")
    migration_command.upgrade(alembic_cfg, "head")


@cli.command(
    name="purge-database",
    help="Drops all tables.",
)
def purge_database(
    no_prompt: bool = typer.Option(False, "--no-prompt", help="Do not prompt for confirmation"),
) -> None:
    """Drop all objects in the database."""
    if not no_prompt:
        confirm = Confirm.ask(
            "[bold red] Are you sure you want to drop everything?",
        )
        if not confirm:
            console.print("Aborting database purge and exiting.")
            sys.exit(0)
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)

    utils.asyncer.run(drop_tables)()


@cli.command(
    name="show-current-database-revision",
    help="Shows the current revision for the database.",
)
def show_database_revision() -> None:
    """Starts the Gluent Console API."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    migration_command.current(alembic_cfg, verbose=False)


async def drop_tables() -> None:
    logger.info("Connecting to database backend.")

    async with engine.begin() as db:
        logger.info("[bold red] Dropping the db")
        BaseModel.metadata.drop_all()
        logger.info("[bold red] Truncating the version table")

        await db.execute(
            DropTable(
                element=Table("ddl_version", meta),
                if_exists=True,
            )
        )
        await db.commit()
    logger.info("Successfully dropped all objects")
