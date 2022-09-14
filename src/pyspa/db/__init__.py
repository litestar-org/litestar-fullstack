import asyncio
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import async_scoped_session

from pyspa.db import db_types
from pyspa.db.engine import async_session_factory, create_async_engine, create_async_session_maker, engine

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


AsyncScopedSession = async_scoped_session(async_session_factory, scopefunc=asyncio.current_task)
"""
Scopes [`AsyncSession`][sqlalchemy.ext.asyncio.AsyncSession] instance to current task using
[`asyncio.current_task()`][asyncio.current_task].

Care must be taken that [`AsyncScopedSession.remove()`][sqlalchemy.ext.asyncio.async_scoped_session.remove]
 is called as late as possible during each task. This is managed by the
 [`Starlite.after_request`][starlite.app.Starlite] lifecycle hook.
"""


async def on_shutdown() -> None:
    """Passed to `Starlite.on_shutdown`."""
    await engine.dispose()


def db_session() -> "AsyncSession":
    return AsyncScopedSession()


__all__ = [
    "create_async_engine",
    "create_async_session_maker",
    "engine",
    "async_session_factory",
    "db_types",
    "AsyncScopedSession",
    "on_shutdown",
    "db_session",
]
