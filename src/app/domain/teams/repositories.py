from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID  # noqa: TCH003

from advanced_alchemy.repository import SQLAlchemyAsyncRepository, SQLAlchemyAsyncSlugRepository
from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import Team, TeamInvitation, TeamMember

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes

__all__ = (
    "TeamInvitationRepository",
    "TeamMemberRepository",
    "TeamRepository",
)


class TeamRepository(SQLAlchemyAsyncSlugRepository[Team]):
    """Team Repository."""

    model_type = Team

    async def get_user_teams(
        self,
        *filters: FilterTypes | ColumnElement[bool],
        user_id: UUID,
        auto_expunge: bool | None = None,
        force_basic_query_mode: bool | None = None,
        **kwargs: Any,
    ) -> tuple[list[Team], int]:
        """Get paginated list and total count of teams that a user can access."""
        team_filter = select(TeamMember.id).where(TeamMember.user_id == user_id)
        return await self.list_and_count(
            *filters,
            Team.id.in_(team_filter),
            statement=select(Team)
            .order_by(Team.name)
            .options(
                selectinload(Team.tags),
                selectinload(Team.members).options(
                    joinedload(TeamMember.user, innerjoin=True),
                ),
            ),
            auto_expunge=auto_expunge,
            force_basic_query_mode=force_basic_query_mode,
            **kwargs,
        )


class TeamMemberRepository(SQLAlchemyAsyncRepository[TeamMember]):
    """Team Member Repository."""

    model_type = TeamMember


class TeamInvitationRepository(SQLAlchemyAsyncRepository[TeamInvitation]):
    """Team Invitation Repository."""

    model_type = TeamInvitation
