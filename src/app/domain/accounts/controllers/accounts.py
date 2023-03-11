"""User Account Controllers."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, noload, subqueryload
from starlite import Controller

from app.domain.accounts.models import User
from app.domain.accounts.services import UserService
from app.domain.teams.models import TeamMember
from app.lib import log

logger = log.get_logger()


def provides_user_service(db_session: AsyncSession) -> UserService:
    """Construct repository and service objects for the request."""
    return UserService(
        session=db_session,
        options=[
            noload("*"),
            subqueryload(User.teams).options(
                joinedload(TeamMember.team, innerjoin=True).options(
                    noload("*"),
                ),
            ),
        ],
    )


class AccountController(Controller):
    """Account Controller."""
