import anyio
from alembic import command as migration_command
from alembic.config import Config as AlembicConfig
from sqlalchemy import Table
from sqlalchemy.schema import DropTable

from app.lib import log, settings

from .base import engine
from .orm import DatabaseModel, meta

logger = log.get_logger()


def create_database() -> None:
    """Create database DDL migrations."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    migration_command.upgrade(alembic_cfg, "head")


def upgrade_database() -> None:
    """Upgrade the database to the latest revision."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    migration_command.upgrade(alembic_cfg, "head")


def reset_database() -> None:
    """Reset the database to an initial empty state."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    anyio.run(drop_tables)
    migration_command.upgrade(alembic_cfg, "head")


def purge_database() -> None:
    """Drop all objects in the database."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    anyio.run(drop_tables)


def show_database_revision() -> None:
    """Show current database revision."""
    alembic_cfg = AlembicConfig(settings.db.MIGRATION_CONFIG)
    alembic_cfg.set_main_option("script_location", settings.db.MIGRATION_PATH)
    migration_command.current(alembic_cfg, verbose=False)


async def drop_tables() -> None:
    """Drop all tables from the database."""
    logger.info("Connecting to database backend.")
    async with engine.begin() as db:
        logger.info("Dropping the db")
        await db.run_sync(DatabaseModel.metadata.drop_all)
        logger.info("Dropping the version table")

        await db.execute(
            DropTable(
                element=Table(settings.db.MIGRATION_DDL_VERSION_TABLE, meta),
                if_exists=True,
            ),
        )
        await db.commit()
    logger.info("Successfully dropped all objects")
