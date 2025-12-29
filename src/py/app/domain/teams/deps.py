"""Team domain dependencies."""

from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.db import models as m
from app.domain.teams.services import TeamMemberService, TeamService
from app.lib.deps import create_service_provider

provide_teams_service = create_service_provider(
    TeamService,
    load=[m.Team.tags, m.Team.members],
    error_messages={"duplicate_key": "This team already exists.", "integrity": "Team operation failed."},
)

provide_team_members_service = create_service_provider(
    TeamMemberService,
    load=[
        selectinload(m.TeamMember.team),
        selectinload(m.TeamMember.user),
    ],
    error_messages={"duplicate_key": "User is already a team member.", "integrity": "Team member operation failed."},
)

__all__ = (
    "provide_team_members_service",
    "provide_teams_service",
)
