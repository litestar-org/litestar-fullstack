"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import joinedload, noload, selectinload

from app.db.models import Team, TeamInvitation, TeamMember
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService

__all__ = ("provide_team_invitations_service", "provide_team_members_service", "provide_teams_service")


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_teams_service(db_session: AsyncSession) -> AsyncGenerator[TeamService, None]:
    """Construct repository and service objects for the request."""
    async with TeamService.new(
        session=db_session,
        load=[
            selectinload(Team.tags),
            selectinload(Team.members).options(
                joinedload(TeamMember.user, innerjoin=True),
            ),
        ],
    ) as service:
        yield service


async def provide_team_members_service(db_session: AsyncSession) -> AsyncGenerator[TeamMemberService, None]:
    """Construct repository and service objects for the request."""
    async with TeamMemberService.new(
        session=db_session,
        load=[
            noload("*"),
            joinedload(TeamMember.team, innerjoin=True).options(noload("*")),
            joinedload(TeamMember.user, innerjoin=True).options(noload("*")),
        ],
    ) as service:
        yield service


async def provide_team_invitations_service(db_session: AsyncSession) -> AsyncGenerator[TeamInvitationService, None]:
    """Construct repository and service objects for the request."""
    async with TeamInvitationService.new(
        session=db_session,
        load=[
            noload("*"),
            joinedload(TeamInvitation.team, innerjoin=True).options(noload("*")),
            joinedload(TeamInvitation.invited_by, innerjoin=True).options(noload("*")),
        ],
    ) as service:
        yield service
