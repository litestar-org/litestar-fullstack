"""Shared-session ServiceGroup bundling team, member, invitation, and tag services."""

from advanced_alchemy.service import ServiceGroup

from app.domain.tags.services import TagService
from app.domain.teams.services._team import TeamService
from app.domain.teams.services._team_invitation import TeamInvitationService
from app.domain.teams.services._team_member import TeamMemberService


class TeamServices(ServiceGroup):
    """Unified team-domain service group sharing a single SQLAlchemy async session."""

    teams: TeamService
    members: TeamMemberService
    invitations: TeamInvitationService
    tags: TagService
