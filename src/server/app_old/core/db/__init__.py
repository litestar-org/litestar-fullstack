from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, cast

from app.config import settings
from app.utils import serializers
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.pool import NullPool
from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin
from starlite.plugins.sql_alchemy.config import (SESSION_SCOPE_KEY,
                                                 SESSION_TERMINUS_ASGI_EVENTS)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
    from starlite.datastructures.state import State
    from starlite.types import Message, Scope

__all__ = ["engine", "async_session_factory", "config", "plugin", "db_engine", "db_session"]


async def before_send_handler(message: "Message", _: "State", scope: "Scope") -> None:
    """Custom `before_send_handler` for SQLAlchemy plugin that inspects the status of response and commits, or rolls back the database.

    Args:
        message: ASGI message
        _:
        scope: ASGI scope
    """
    db_session = cast("AsyncSession | None", scope.get(SESSION_SCOPE_KEY))
    try:
        if db_session is not None and message["type"] == "http.response.start":
            if 200 <= message["status"] < 300:
                await db_session.commit()
            else:
                await db_session.rollback()
    finally:
        if db_session is not None and message["type"] in SESSION_TERMINUS_ASGI_EVENTS:
            await db_session.close()
            del scope[SESSION_SCOPE_KEY]  # type:ignore[misc]


engine = create_async_engine(
    settings.db.URL,
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
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)
"""
Database session factory. See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
"""
config = SQLAlchemyConfig(
    dependency_key="db_session",
    engine_instance=engine,
    session_maker_instance=async_session_factory,
    before_send_handler=before_send_handler,
)


plugin = SQLAlchemyPlugin(config=config)


@asynccontextmanager
async def db_session() -> "AsyncIterator[AsyncSession]":
    """Use this to get a database session where you can't in starlite.

    Returns:
        config.session_class: _description_
    """
    async with async_session_factory() as session:
        yield session


def db_engine() -> "AsyncEngine":
    """Fetch the db engine.

    Returns:
        config.session_class: _description_
    """
    return engine
