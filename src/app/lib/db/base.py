from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from starlite.contrib.sqlalchemy_1.config import SESSION_SCOPE_KEY, SESSION_TERMINUS_ASGI_EVENTS, SQLAlchemyConfig
from starlite.contrib.sqlalchemy_1.plugin import SQLAlchemyPlugin
from starlite.status_codes import HTTP_200_OK, HTTP_300_MULTIPLE_CHOICES

from app.lib import constants, serialization, settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession
    from starlite.datastructures.state import State
    from starlite.types import Message, Scope


async def before_send_handler(message: Message, _: State, scope: Scope) -> None:
    """Handle database connection before sending response.

    Custom `before_send_handler` for SQLAlchemy plugin that inspects the status of response and commits, or rolls back the database.

    Args:
        message: ASGI message
        _:
        scope: ASGI scope
    """
    db_session = cast("AsyncSession | None", scope.get(SESSION_SCOPE_KEY))
    try:
        if db_session is not None and message["type"] == "http.response.start":
            if HTTP_200_OK <= message["status"] < HTTP_300_MULTIPLE_CHOICES:
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
"""
Database session factory. See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
"""
config = SQLAlchemyConfig(
    dependency_key=constants.DB_SESSION_DEPENDENCY_KEY,
    engine_instance=engine,
    session_maker_instance=async_session_factory,
    before_send_handler=before_send_handler,
)


plugin = SQLAlchemyPlugin(config=config)


@asynccontextmanager
async def session() -> AsyncIterator[AsyncSession]:
    """Use this to get a database session where you can't in starlite.

    Returns:
        config.session_class: _description_
    """
    async with async_session_factory() as session:
        yield session
