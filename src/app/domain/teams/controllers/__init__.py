"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TCH002
from sqlalchemy.orm import joinedload, noload, selectinload
from starlite import Controller
from starlite.di import Provide

from app.domain.teams.models import Team, TeamMember
from app.domain.teams.services import TeamService
from app.lib import log

__all__ = ["TeamController", "provides_teams_service"]


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


logger = log.get_logger()


async def provides_teams_service(db_session: AsyncSession) -> AsyncGenerator[TeamService, None]:
    """Construct repository and service objects for the request."""
    async with TeamService.new(
        session=db_session,
        base_select=select(Team).options(
            noload("*"),
            selectinload(Team.members).options(
                joinedload(TeamMember.user, innerjoin=True).options(
                    noload("*"),
                ),
            ),
        ),
    ) as service:
        try:
            yield service
        finally:
            ...


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = {"teams_service": Provide(provides_teams_service)}
