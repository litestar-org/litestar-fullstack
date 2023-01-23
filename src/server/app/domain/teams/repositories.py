from app.lib import db

from .models import Team, TeamInvitation, TeamMember

__all__ = ["TeamRepository", "TeamMemberRepository", "TeamInvitationRepository"]


class TeamRepository(db.SQLAlchemyRepository[Team]):
    """Team Repository."""


class TeamMemberRepository(db.SQLAlchemyRepository[TeamMember]):
    """Team Member Repository."""


class TeamInvitationRepository(db.SQLAlchemyRepository[TeamInvitation]):
    """Team Invitation Repository."""
