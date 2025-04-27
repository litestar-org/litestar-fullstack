"""User Account Controllers."""

from __future__ import annotations

from litestar import Controller

from app.lib.deps import create_service_provider
from app.services import TeamInvitationService


class TeamInvitationController(Controller):
    """Team Invitations."""

    tags = ["Teams"]
    dependencies = {"team_invitations_service": create_service_provider(TeamInvitationService)}
