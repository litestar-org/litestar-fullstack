"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import joinedload, noload, selectinload

from app.db.models import Team, TeamInvitation, TeamMember
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService

__all__ = ["provide_team_members_service", "provides_teams_service", "provide_team_invitations_service"]


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provides_teams_service(db_session: AsyncSession) -> AsyncGenerator[TeamService, None]:
    """Construct repository and service objects for the request."""
    async with TeamService.new(
        session=db_session,
        statement=select(Team)
        .order_by(Team.name)
        .options(
            selectinload(Team.tags).options(noload("*")),
            selectinload(Team.members).options(
                joinedload(TeamMember.user, innerjoin=True).options(noload("*")),
            ),
        ),
    ) as service:
        try:
            yield service
        finally:
            ...


async def provide_team_members_service(db_session: AsyncSession) -> AsyncGenerator[TeamMemberService, None]:
    """Construct repository and service objects for the request."""
    async with TeamMemberService.new(
        session=db_session,
        statement=select(TeamMember).options(
            noload("*"),
            joinedload(TeamMember.team, innerjoin=True).options(noload("*")),
            joinedload(TeamMember.user, innerjoin=True).options(noload("*")),
        ),
    ) as service:
        try:
            yield service
        finally:
            ...


async def provide_team_invitations_service(db_session: AsyncSession) -> AsyncGenerator[TeamInvitationService, None]:
    """Construct repository and service objects for the request."""
    async with TeamInvitationService.new(
        session=db_session,
        statement=select(TeamInvitation).options(
            noload("*"),
            joinedload(TeamInvitation.team, innerjoin=True).options(noload("*")),
            joinedload(TeamInvitation.invited_by, innerjoin=True).options(noload("*")),
        ),
    ) as service:
        try:
            yield service
        finally:
            ...
