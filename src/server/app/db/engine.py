from functools import partial
from typing import TYPE_CHECKING, Any
from uuid import UUID

from orjson import dumps
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

if TYPE_CHECKING:
    from app.config.application import Settings


def _default(val: Any) -> str:
    if isinstance(val, UUID):
        return str(val)
    raise TypeError()


def create_async_engine(settings: "Settings") -> "AsyncEngine":
    engine = _create_async_engine(
        settings.db.URL,
        echo=settings.db.ECHO,
        echo_pool=settings.db.ECHO_POOL,
        json_serializer=partial(dumps, default=_default),
        max_overflow=settings.db.POOL_MAX_OVERFLOW,
        pool_size=settings.db.POOL_SIZE,
        pool_timeout=settings.db.POOL_TIMEOUT,
        pool_recycle=settings.db.POOL_RECYCLE,
        pool_pre_ping=settings.db.POOL_PRE_PING,
        poolclass=NullPool if settings.db.POOL_DISABLE else None,
    )
    dialect_name = engine.dialect.name
    # Special tweak for SQLite to better handle transaction
    # See: https://docs.sqlalchemy.org/en/14/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
    if dialect_name == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def do_connect(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None

            # Enable SQLite foreign key support, which is not enabled by default
            # See: https://www.sqlite.org/foreignkeys.html#fk_enable
            dbapi_connection.execute("pragma foreign_keys=ON")

        @event.listens_for(engine.sync_engine, "begin")
        def do_begin(conn):  # type: ignore[no-untyped-def]
            # emit our own BEGIN
            conn.exec_driver_sql("BEGIN")

    return engine


def create_async_session_maker(engine: "AsyncEngine") -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


"""
Configure via [Settings][app.config.application.Settings].
Overrides default JSON serializer to use `orjson`.
See [`create_async_engine()`][sqlalchemy.ext.asyncio.create_async_engine]
 for detailed instructions.
"""
engine = create_async_engine(settings)
"""
Database engine. See [`create_async_engine()`][sqlalchemy.ext.asyncio.engine].
"""
async_session_factory = create_async_session_maker(engine)
"""
Database session factory. See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
"""
