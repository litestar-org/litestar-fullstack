from starlite.contrib.sqlalchemy.repository import SQLAlchemyRepository

from app.domain.teams.models import Team, TeamInvitation, TeamMember
from app.lib.service.sqlalchemy import SQLAlchemyRepositoryService


class TeamRepository(SQLAlchemyRepository[Team]):
    """Team Repository."""

    model_type = Team


class TeamService(SQLAlchemyRepositoryService[Team]):
    """Team Service."""

    repository_type = TeamRepository


class TeamMemberRepository(SQLAlchemyRepository[TeamMember]):
    """Team Member Repository."""

    model_type = TeamMember


class TeamMemberService(SQLAlchemyRepositoryService[TeamMember]):
    """Team Member Service."""

    repository_type = TeamMemberRepository


class TeamInvitationRepository(SQLAlchemyRepository[TeamInvitation]):
    """Team Invitation Repository."""

    model_type = TeamInvitation


class TeamInvitationService(SQLAlchemyRepositoryService[TeamInvitation]):
    """Team Invitation Service."""

    repository_type = TeamInvitationRepository
