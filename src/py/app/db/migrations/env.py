# ruff: noqa: ARG001
import asyncio
from typing import TYPE_CHECKING, Literal, cast

from advanced_alchemy.base import metadata_registry
from alembic import context
from alembic.autogenerate import rewriter
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config
from sqlalchemy.sql.schema import SchemaItem

if TYPE_CHECKING:
    from advanced_alchemy.alembic.commands import AlembicCommandConfig
    from sqlalchemy.engine import Connection

__all__ = ("do_run_migrations", "run_migrations_offline", "run_migrations_online")


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config: "AlembicCommandConfig" = context.config  # type: ignore
writer = rewriter.Rewriter()


def include_object(
    obj: SchemaItem,
    name: str | None,
    type_: Literal[
        "schema",
        "table",
        "column",
        "index",
        "unique_constraint",
        "foreign_key_constraint",
    ],
    reflected: bool,
    compare_to: SchemaItem | None,
) -> bool:
    """Excludes the SAQ tables, indexes, and other objects from being included in autogeneration

    Args:
        obj: The object to include.
        name: The name of the object.
        type_: The type of the object.
        reflected: Whether the object is reflected.
        compare_to: The object to compare to.

    Returns:
        Whether the object should be included.
    """
    return not (
        (name is not None and name.startswith("saq_"))
        or (type_ == "table" and name in {"task_queue", "task_queue_stats", "task_queue_ddl_version"})
        or (name is not None and name == "task_queue_lock_key_seq")
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    context.configure(
        url=config.db_url,
        target_metadata=metadata_registry.get(config.bind_key),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=config.compare_type,
        version_table=config.version_table_name,
        version_table_pk=config.version_table_pk,
        user_module_prefix=config.user_module_prefix,
        render_as_batch=config.render_as_batch,
        process_revision_directives=writer,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: "Connection") -> None:
    """Run migrations."""
    context.configure(
        connection=connection,
        target_metadata=metadata_registry.get(config.bind_key),
        compare_type=config.compare_type,
        version_table=config.version_table_name,
        version_table_pk=config.version_table_pk,
        user_module_prefix=config.user_module_prefix,
        render_as_batch=config.render_as_batch,
        process_revision_directives=writer,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.

    Raises:
        RuntimeError: If the engine cannot be created from the config.
    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = config.db_url

    connectable = cast(
        "AsyncEngine",
        config.engine
        or async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        ),
    )
    if connectable is None:  # pyright: ignore[reportUnnecessaryComparison]
        msg = "Could not get engine from config.  Please ensure your `alembic.ini` according to the official Alembic documentation."
        raise RuntimeError(
            msg,
        )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
