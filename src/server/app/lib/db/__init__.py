"""Core DB Package."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

from starlite_saqlalchemy.db import async_session_factory, engine
from starlite_saqlalchemy.repository.sqlalchemy import SQLAlchemyRepository
from starlite_saqlalchemy.sqlalchemy_plugin import SQLAlchemyHealthCheck, before_send_handler, config, plugin

from . import orm, utils

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = [
    "orm",
    "utils",
    "before_send_handler",
    "SQLAlchemyHealthCheck",
    "config",
    "plugin",
    "engine",
    "session",
    "async_session_factory",
    "SQLAlchemyRepository",
]


@asynccontextmanager
async def session() -> AsyncIterator[AsyncSession]:
    """Use this to get a database session where you can't in starlite.

    Returns:
        config.session_class: _description_
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
