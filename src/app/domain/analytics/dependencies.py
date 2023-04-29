"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

import aiosql

from app.lib.db.base import SQLAlchemyAiosqlQueryManager

__all__ = ["provides_user_analytic_queries"]


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


user_analytic_queries = aiosql.from_str(
    """
--name: users-by-week
select a.week, count(a.user_id) as new_users
from (
    select date_trunc('week', user_account.created) as week, user_account.id as user_id
    from user_account
) a
group by a.week
order by a.week
""",
    driver_adapter="asyncpg",
)


async def provides_user_analytic_queries(
    db_session: AsyncSession,
) -> AsyncGenerator[SQLAlchemyAiosqlQueryManager, None]:
    """Construct repository and service objects for the request."""
    async with SQLAlchemyAiosqlQueryManager.from_session(user_analytic_queries, session=db_session) as query_manager:
        yield query_manager
