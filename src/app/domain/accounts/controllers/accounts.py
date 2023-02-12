"""User Account Controllers."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, noload, subqueryload
from starlite import Controller

from app.domain.teams.models import TeamMember
from app.lib import log

from ..models import User
from ..services import UserService

logger = log.getLogger()


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
