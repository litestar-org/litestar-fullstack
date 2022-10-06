from contextlib import contextmanager
from typing import TYPE_CHECKING, cast

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.pool import NullPool
from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyEngineConfig, SQLAlchemySessionConfig

from app.config import settings
from app.utils import serializers

if TYPE_CHECKING:
    from collections.abc import Iterator


engine_config = SQLAlchemyEngineConfig(
    future=True,
    json_serializer=serializers.serialize_object,
    json_deserializer=serializers.deserialize_object,
    echo=settings.db.ECHO,
    echo_pool=True if settings.db.ECHO_POOL == "debug" else settings.db.ECHO_POOL,
    max_overflow=settings.db.POOL_MAX_OVERFLOW,
    pool_size=settings.db.POOL_SIZE,
    pool_timeout=settings.db.POOL_TIMEOUT,
    pool_recycle=settings.db.POOL_RECYCLE,
    pool_pre_ping=settings.db.POOL_PRE_PING,
    poolclass=NullPool if settings.db.POOL_DISABLE else None,
    connect_args=settings.db.CONNECT_ARGS,
)
session_config = SQLAlchemySessionConfig(expire_on_commit=False, autoflush=False)
config = SQLAlchemyConfig(
    connection_string=settings.db.URL,
    engine_config=engine_config,
    session_config=session_config,
    session_maker_app_state_key="db_session_maker",
)


@contextmanager
def db_session() -> "Iterator[AsyncSession]":
    """Use this to get a database session where you can't in starlite

    Returns:
        config.session_class: _description_
    """
    try:
        session = config.session_maker()
        yield session
    finally:
        session.close()


def db_engine() -> "AsyncEngine":
    """Fetch the db engine

    Returns:
        config.session_class: _description_
    """
    return cast("AsyncEngine", config.engine)


__all__ = [
    "config",
    "session_config",
    "engine_config",
    "db_types",
    "db_session",
    "db_engine",
    "models",
    "repositories",
]
