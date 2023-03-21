from app.domain.teams.models import Team, TeamInvitation, TeamMember
from app.lib.service.sqlalchemy import SQLAlchemyRepositoryService

__all__ = ["TeamService", "TeamInvitationService", "TeamMemberService"]


class TeamService(SQLAlchemyRepositoryService[Team]):
    """Team Service."""


class TeamMemberService(SQLAlchemyRepositoryService[TeamMember]):
    """Team Member Service."""


class TeamInvitationService(SQLAlchemyRepositoryService[TeamInvitation]):
    """Team Invitation Service."""
