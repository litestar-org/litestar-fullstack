"""User Account Controllers."""
from __future__ import annotations

from litestar import Controller
from litestar.di import Provide

from app.domain.teams.dependencies import provide_team_invitations_service

__all__ = ["TeamInvitationController", "provide_team_invitations_service"]


class TeamInvitationController(Controller):
    """Team Invitations."""

    tags = ["Teams"]
    dependencies = {"team_invitations_service": Provide(provide_team_invitations_service)}
