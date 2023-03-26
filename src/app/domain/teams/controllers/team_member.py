"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TCH002
from sqlalchemy.orm import joinedload, noload
from starlite import Controller
from starlite.di import Provide

from app.domain.teams.models import TeamMember
from app.domain.teams.services import TeamMemberService
from app.lib import log

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


logger = log.get_logger()


async def provide_team_members_service(db_session: AsyncSession) -> AsyncGenerator[TeamMemberService, None]:
    """Construct repository and service objects for the request."""
    async with TeamMemberService.new(
        session=db_session,
        base_select=select(TeamMember).options(
            noload("*"),
            joinedload(TeamMember.team, innerjoin=True).options(
                noload("*"),
            ),
            joinedload(TeamMember.user, innerjoin=True).options(
                noload("*"),
            ),
        ),
    ) as service:
        try:
            yield service
        finally:
            ...


class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Teams"]
    dependencies = {"team_members_service": Provide(provide_team_members_service)}
