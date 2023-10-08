"""User Account Controllers."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import aiosql
from litestar_aiosql.service import AiosqlQueryManager

from app.lib.exceptions import ApplicationError
from app.lib.settings import BASE_DIR

__all__ = ["provides_analytic_queries"]


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


analytics_queries = aiosql.from_path(Path(BASE_DIR / "domain" / "analytics" / "sql"), driver_adapter="asyncpg")


async def provides_analytic_queries(
    db_session: AsyncSession,
) -> AsyncGenerator[AiosqlQueryManager, None]:
    """Construct repository and service objects for the request."""
    db_connection = await db_session.connection()
    raw_connection = await db_connection.get_raw_connection()
    if not raw_connection.driver_connection:
        msg = "Unable to fetch raw connection from session."
        raise ApplicationError(msg)
    async with AiosqlQueryManager.from_connection(
        analytics_queries,
        connection=raw_connection.driver_connection,
    ) as query_manager:
        yield query_manager
