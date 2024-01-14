"""User Account Controllers."""
from __future__ import annotations

from litestar import Controller
from litestar.di import Provide

from app.domain.teams.dependencies import provide_team_members_service


class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Teams"]
    dependencies = {"team_members_service": Provide(provide_team_members_service)}
