from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository, SQLAlchemyAsyncSlugRepository

from app.db.models import Team, TeamInvitation, TeamMember

__all__ = (
    "TeamInvitationRepository",
    "TeamMemberRepository",
    "TeamRepository",
)


class TeamRepository(SQLAlchemyAsyncSlugRepository[Team]):
    """Team Repository."""

    model_type = Team


class TeamMemberRepository(SQLAlchemyAsyncRepository[TeamMember]):
    """Team Member Repository."""

    model_type = TeamMember


class TeamInvitationRepository(SQLAlchemyAsyncRepository[TeamInvitation]):
    """Team Invitation Repository."""

    model_type = TeamInvitation
