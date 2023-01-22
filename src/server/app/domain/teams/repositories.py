from app.lib import db

from .models import Team, TeamInvitation, TeamMember


class TeamRepository(db.SQLAlchemyRepository[Team]):
    """Team Repository."""


class TeamMemberRepository(db.SQLAlchemyRepository[TeamMember]):
    """Team Member Repository."""


class TeamInvitationRepository(db.SQLAlchemyRepository[TeamInvitation]):
    """Team Invitation Repository."""
