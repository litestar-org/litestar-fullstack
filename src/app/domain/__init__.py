"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from . import accounts, openapi, security, teams, urls, web

if TYPE_CHECKING:
    from starlite.types import ControllerRouterHandler

routes: list[ControllerRouterHandler] = [
    accounts.controllers.AccessController,
    accounts.controllers.AccountController,
    teams.controllers.TeamController,
    teams.controllers.TeamInvitationController,
    teams.controllers.TeamMemberController,
    web.controllers.WebController,
]

__all__ = ["accounts", "examples", "teams", "web", "urls", "security", "routes", "openapi"]
