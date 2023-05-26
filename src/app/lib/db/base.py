from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, cast

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
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.lib import constants, serialization, settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from litestar.types import Message, Scope
    from sqlalchemy.ext.asyncio import AsyncSession
__all__ = ["before_send_handler", "session"]


async def before_send_handler(message: Message, scope: Scope) -> None:
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


@event.listens_for(engine.sync_engine, "connect")
def _sqla_on_connect(dbapi_connection: Any, _: Any) -> Any:  # pragma: no cover
    """Using msgspec for serialization of the json column values means that the
    output is binary, not `str` like `json.dumps` would output.
    SQLAlchemy expects that the json serializer returns `str` and calls `.encode()` on the value to
    turn it to bytes before writing to the JSONB column. I'd need to either wrap `serialization.to_json` to
    return a `str` so that SQLAlchemy could then convert it to binary, or do the following, which
    changes the behaviour of the dialect to expect a binary value from the serializer.
    See Also https://github.com/sqlalchemy/sqlalchemy/blob/14bfbadfdf9260a1c40f63b31641b27fe9de12a0/lib/sqlalchemy/dialects/postgresql/asyncpg.py#L934  pylint: disable=line-too-long
    """

    def encoder(bin_value: bytes) -> bytes:
        return b"\x01" + serialization.to_json(bin_value)

    def decoder(bin_value: bytes) -> Any:
        # the byte is the \x01 prefix for jsonb used by PostgreSQL.
        # asyncpg returns it when format='binary'
        return serialization.from_json(bin_value[1:])

    dbapi_connection.await_(
        dbapi_connection.driver_connection.set_type_codec(
            "jsonb",
            encoder=encoder,
            decoder=decoder,
            schema="pg_catalog",
            format="binary",
        )
    )
    dbapi_connection.await_(
        dbapi_connection.driver_connection.set_type_codec(
            "json",
            encoder=encoder,
            decoder=decoder,
            schema="pg_catalog",
            format="binary",
        )
    )


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
