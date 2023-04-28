from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast

from litestar.contrib.sqlalchemy.plugins.init.config import (
    SQLAlchemyAsyncConfig,
)
from litestar.contrib.sqlalchemy.plugins.init.config.common import SESSION_SCOPE_KEY, SESSION_TERMINUS_ASGI_EVENTS
from litestar.contrib.sqlalchemy.plugins.init.plugin import SQLAlchemyInitPlugin
from litestar.status_codes import HTTP_200_OK, HTTP_300_MULTIPLE_CHOICES
from litestar.utils import (
    delete_litestar_scope_state,
    get_litestar_scope_state,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.lib import constants, serialization, settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from aiosql.queries import Queries
    from litestar.datastructures.state import State
    from litestar.types import Message, Scope
    from sqlalchemy.engine.interfaces import DBAPIConnection
    from sqlalchemy.ext.asyncio import AsyncSession
__all__ = ["before_send_handler", "session", "QueryManager"]


async def before_send_handler(message: Message, _: State, scope: Scope) -> None:
    """Handle database connection before sending response.

    Custom `before_send_handler` for SQLAlchemy plugin that inspects the status of response and commits, or rolls back the database.

    Args:
        message: ASGI message
        _:
        scope: ASGI scope
    """
    session = cast("AsyncSession | None", get_litestar_scope_state(scope, SESSION_SCOPE_KEY))
    try:
        if session is not None and message["type"] == "http.response.start":
            if HTTP_200_OK <= message["status"] < HTTP_300_MULTIPLE_CHOICES:
                await session.commit()
            else:
                await session.rollback()
    finally:
        if session and message["type"] in SESSION_TERMINUS_ASGI_EVENTS:
            await session.close()
            delete_litestar_scope_state(scope, SESSION_SCOPE_KEY)


engine = create_async_engine(
    settings.db.URL,
    future=True,
    json_serializer=serialization.to_json,
    json_deserializer=serialization.from_json,
    echo=settings.db.ECHO,
    echo_pool=True if settings.db.ECHO_POOL == "debug" else settings.db.ECHO_POOL,
    max_overflow=settings.db.POOL_MAX_OVERFLOW,
    pool_size=settings.db.POOL_SIZE,
    pool_timeout=settings.db.POOL_TIMEOUT,
    pool_recycle=settings.db.POOL_RECYCLE,
    pool_pre_ping=settings.db.POOL_PRE_PING,
    pool_use_lifo=True,  # use lifo to reduce the number of idle connections
    poolclass=NullPool if settings.db.POOL_DISABLE else None,
    connect_args=settings.db.CONNECT_ARGS,
)
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)
"""Database session factory.

See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
"""
config = SQLAlchemyAsyncConfig(
    session_dependency_key=constants.DB_SESSION_DEPENDENCY_KEY,
    engine_instance=engine,
    session_maker=async_session_factory,
    before_send_handler=before_send_handler,
)


plugin = SQLAlchemyInitPlugin(config=config)


@asynccontextmanager
async def session() -> AsyncIterator[AsyncSession]:
    """Use this to get a database session where you can't in litestar.

    Returns:
        AsyncIterator[AsyncSession]
    """
    async with async_session_factory() as session:
        yield session


class QueryManager:
    def __init__(self, db_connection: DBAPIConnection, queries: Queries) -> None:
        self.db_connection = db_connection
        self.queries = queries
