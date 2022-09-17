import binascii
import logging
import os
import sys
from typing import Any, AsyncGenerator, Optional

import click
from alembic import command as migration_command
from alembic.config import Config as AlembicConfig
from pydantic import EmailStr, SecretStr
from rich.prompt import Confirm
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.schema import DropTable

from pyspa import schemas, services, utils
from pyspa.asgi import app
from pyspa.cli.console import console
from pyspa.config import settings
from pyspa.db import engine
from pyspa.models import BaseModel, meta

logger = logging.getLogger()


@click.group(name="manage", invoke_without_command=False)
@click.pass_context
def cli(_: dict[str, Any]) -> None:
    """System Administration Commands"""


@cli.command(name="generate-random-key")
def generate_random_key(length: int = 32) -> None:
    """Helper for admins to generate random 26 character string.

    Used as the secret key for sessions.
    Must be consistent (and secret) per environment.
    Output: b'random2323db3....1xyz'
    Copy the value in between the quotation marks to the settings file
    """
    console.print(binascii.hexlify(os.urandom(length)))


@cli.command(name="create-user", help="Create a user")
@click.option(
    "--email",
    help="Email of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--full-name",
    help="Full name of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--password",
    help="Password",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--team-name",
    help="Team Name",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--superuser",
    help="Is a superuser",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=False,
)
def create_user(
    email: Optional[str],
    full_name: Optional[str],
    password: Optional[str],
    team_name: Optional[str],
    superuser: Optional[bool],
) -> None:
    """Create a user"""

    email = email or click.prompt("Email")
    full_name = full_name or click.prompt("Full Name", show_default=False)
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    team_name = team_name or click.prompt("Initial Team Name", show_default=True)
    superuser = superuser or click.prompt("Create as superuser?", show_default=True, type=click.BOOL)
    obj_in = schemas.UserSignup(
        email=EmailStr(email), full_name=full_name, password=SecretStr(password), team_name=team_name
    )

    async def _create_user(obj_in: schemas.UserSignup) -> None:
        async with engine.begin() as db:
            user = await services.user.create(db=db, obj_in=obj_in)
            console.print(f"User created: {user.email}")

    utils.asyncer.run(_create_user)(obj_in)


@cli.command(name="promote-to-superuser", help="Promotes a user to application superuser")
@click.option(
    "--email",
    help="Email of the user",
    type=click.STRING,
    required=False,
    show_default=False,
)
def promote_to_superuser(email: Optional[str]) -> None:
    """Promotes a user to application superuser"""
    email = email or click.prompt("Email")

    async def _promote_to_superuser(email: EmailStr) -> None:
        async with engine.begin() as db:
            user = await services.user.get_by_email(db=db, email=email)
            if user:
                console.print(f"Promoting user: {user.email}")
                user_in = schemas.UserUpdate(
                    email=user.email,
                    is_superuser=True,
                )
                user = await services.user.update(db_obj=user, obj_in=user_in, db=db)  # type: ignore
                console.print(f"Upgraded {email} to superuser")
            else:
                console.print(f"User not found: {email}")

    utils.asyncer.run(_promote_to_superuser)(email=email)


@cli.command(
    name="export-openapi-schema",
)
@click.option(
    "--export-path",
    help="Path to export the openapi schema.",
    type=click.STRING,
    default=".",
    required=False,
    show_default=False,
)
def export_api_schema(options: dict[str, Any]) -> None:
    """Push secrets to Secrets Provider"""
    export_location = options.get("export_location", ".")
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
def create_database(options: dict[str, Any]) -> None:
    """Create database DDL migrations."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    migration_command.upgrade(alembic_cfg, "head")


@cli.command(
    name="upgrade-database",
    help="Executes migrations to apply any outstanding database structures.",
)
def upgrade_database(options: dict[str, Any]) -> None:
    """Upgrade the database to the latest revision."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    migration_command.upgrade(alembic_cfg, "head")


@cli.command(
    name="reset-database",
    help="Executes migrations to apply any outstanding database structures.",
)
@click.option(
    "--no-prompt",
    help="Do not prompt for confirmation.",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=True,
)
def reset_database(options: dict[str, Any]) -> None:
    """Resets the database to an initial empty state."""
    no_prompt = options.get("no_prompt", False)
    if not no_prompt:
        Confirm.ask(
            "[bold red] Are you sure you want to drop and recreate everything?",
        )
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)

    utils.asyncer.run(drop_tables)()

    console.log("Recreating the db")
    migration_command.upgrade(alembic_cfg, "head")


@cli.command(
    name="purge-database",
    help="Drops all tables.",
)
@click.option(
    "--no-prompt",
    help="Do not prompt for confirmation.",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=True,
)
def purge_database(options: dict[str, Any]) -> None:
    """Drop all objects in the database."""
    no_prompt = options.get("no_prompt", False)
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
        await db.run_sync(BaseModel.metadata.drop_all)
        logger.info("[bold red] Dropping the version table")

        await db.execute(
            DropTable(
                element=Table(settings.db.MIGRATION_DDL_VERSION_TABLE, meta),
                if_exists=True,
            )
        )
        await db.commit()
    logger.info("Successfully dropped all objects")


async def _db() -> AsyncGenerator[AsyncConnection, None]:

    async with engine.begin() as db:
        yield db
