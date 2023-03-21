from starlite.contrib.sqlalchemy.repository import SQLAlchemyRepository

from .models import Team, TeamInvitation, TeamMember

__all__ = ["TeamRepository", "TeamMemberRepository", "TeamInvitationRepository"]


class TeamRepository(SQLAlchemyRepository[Team]):
    """Team Repository."""


class TeamMemberRepository(SQLAlchemyRepository[TeamMember]):
    """Team Member Repository."""


class TeamInvitationRepository(SQLAlchemyRepository[TeamInvitation]):
    """Team Invitation Repository."""
