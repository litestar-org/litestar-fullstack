"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from . import accounts, analytics, openapi, security, teams, urls, web

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler

routes: list[ControllerRouterHandler] = [
    accounts.controllers.AccessController,
    accounts.controllers.AccountController,
    teams.controllers.TeamController,
    # teams.controllers.TeamInvitationController,
    # teams.controllers.TeamMemberController,
    analytics.controllers.StatsController,
    web.controllers.WebController,
]

__all__ = ["accounts", "teams", "web", "urls", "security", "routes", "openapi", "analytics"]
