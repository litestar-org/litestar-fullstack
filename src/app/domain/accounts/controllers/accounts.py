"""User Account Controllers."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, noload, subqueryload
from starlite import Controller

from app.domain.accounts.models import User
from app.domain.accounts.services import UserService
from app.domain.teams.models import TeamMember
from app.lib import log

logger = log.get_logger()


async def provides_user_service(db_session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Construct repository and service objects for the request."""
    async with UserService.new(
        session=db_session,
        base_select=select(User).options(
            noload("*"),
            subqueryload(User.teams).options(
                joinedload(TeamMember.team, innerjoin=True).options(
                    noload("*"),
                ),
            ),
        ),
    ) as service:
        try:
            yield service
        finally:
            ...


class AccountController(Controller):
    """Account Controller."""
