"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TCH002
from sqlalchemy.orm import joinedload, noload
from starlite import Controller
from starlite.di import Provide

from app.domain.teams.models import TeamInvitation
from app.domain.teams.services import TeamInvitationService
from app.lib import log

__all__ = ["TeamInvitationController", "provide_team_invitations_service"]


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


logger = log.get_logger()


async def provide_team_invitations_service(db_session: AsyncSession) -> AsyncGenerator[TeamInvitationService, None]:
    """Construct repository and service objects for the request."""
    async with TeamInvitationService.new(
        session=db_session,
        base_select=select(TeamInvitation).options(
            noload("*"),
            joinedload(TeamInvitation.team, innerjoin=True).options(
                noload("*"),
            ),
            joinedload(TeamInvitation.invited_by, innerjoin=True).options(
                noload("*"),
            ),
        ),
    ) as service:
        try:
            yield service
        finally:
            ...


class TeamInvitationController(Controller):
    """Team Invitations."""

    tags = ["Teams"]
    dependencies = {"team_invitations_service": Provide(provide_team_invitations_service)}
