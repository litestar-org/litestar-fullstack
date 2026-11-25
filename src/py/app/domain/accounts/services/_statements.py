"""Statement building blocks shared by the account services."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError
from sqlalchemy.orm import joinedload, selectinload

from app.db import models as m

if TYPE_CHECKING:
    from advanced_alchemy.exceptions import IntegrityError
    from sqlalchemy import CursorResult, Delete, Update
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio.scoping import async_scoped_session

__all__ = ("ACCOUNT_STATE_LOAD", "affected_rows", "is_constraint_violation")

ACCOUNT_STATE_LOAD = (
    selectinload(m.User.roles).options(joinedload(m.UserRole.role, innerjoin=True)),
    selectinload(m.User.teams).options(joinedload(m.TeamMember.team, innerjoin=True)),
    selectinload(m.User.mfa_factors),
)
"""Relationships a user needs loaded before authorization or ``UserService.to_account_state`` reads it."""


async def affected_rows(
    db_session: AsyncSession | async_scoped_session[AsyncSession],
    statement: Update | Delete,
) -> int:
    """Execute a conditional ``UPDATE`` or ``DELETE`` inside the caller's transaction.

    Returns:
        Number of rows the statement changed.
    """
    cursor_result = cast("CursorResult[Any]", await db_session.execute(statement))
    return cursor_result.rowcount


def is_constraint_violation(error: IntegrityError) -> bool:
    """Tell whether an Advanced Alchemy ``IntegrityError`` reports a row the database refused to store.

    Advanced Alchemy raises ``IntegrityError`` for every statement that fails, including a lost connection,
    a lock timeout, and a missing table. Only a violated constraint means the row conflicts with stored data,
    so callers answering "duplicate" or "conflict" check here first and re-raise everything else.

    Returns:
        ``True`` when a unique, foreign key, not-null, or check constraint rejected the statement.
    """
    return isinstance(error.__cause__, SQLAlchemyIntegrityError)
