"""Statement building blocks shared by the system jobs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy import ColumnElement, FromClause
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import DeclarativeBase

__all__ = ("count_rows",)


async def count_rows(
    db_session: AsyncSession,
    source: FromClause | type[DeclarativeBase],
    criterion: ColumnElement[bool],
) -> int:
    """Count the rows of ``source`` that match ``criterion`` inside the caller's transaction.

    Returns:
        Number of matching rows.
    """
    return await db_session.scalar(select(func.count()).select_from(source).where(criterion)) or 0
