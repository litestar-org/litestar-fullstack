from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID  # noqa: TCH003

from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import Team, TeamInvitation, TeamMember
from app.lib.repository import SQLAlchemyAsyncRepository, SQLAlchemyAsyncSlugRepository

if TYPE_CHECKING:
    from app.lib.dependencies import FilterTypes

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

        return await self.list_and_count(
            *filters,
            statement=select(Team)
            .join(TeamMember, onclause=Team.id == TeamMember.team_id, isouter=False)
            .where(TeamMember.user_id == user_id)
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
