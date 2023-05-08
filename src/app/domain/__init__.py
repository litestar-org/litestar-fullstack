"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from . import accounts, analytics, openapi, security, system, teams, urls, web

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler
    from saq import CronJob

    from app.lib.worker import WorkerFunction


routes: list[ControllerRouterHandler] = [
    accounts.controllers.AccessController,
    accounts.controllers.AccountController,
    teams.controllers.TeamController,
    # teams.controllers.TeamInvitationController,
    # teams.controllers.TeamMemberController,
    analytics.controllers.StatsController,
    system.controllers.SystemController,
    web.controllers.WebController,
]

__all__ = [
    "tasks",
    "scheduled_tasks",
    "system",
    "accounts",
    "teams",
    "web",
    "urls",
    "security",
    "routes",
    "openapi",
    "analytics",
]
tasks: list[WorkerFunction] = []
scheduled_tasks: list[CronJob] = []
