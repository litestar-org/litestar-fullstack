"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.lib import settings, worker
from app.lib.worker.controllers import WorkerController

from . import accounts, analytics, openapi, security, system, teams, urls, web

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler


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

if settings.worker.WEB_ENABLED:
    routes.append(WorkerController)

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
tasks: dict[worker.Queue, list[worker.WorkerFunction]] = {
    worker.queues.get("system"): [  # type: ignore[dict-item]
        worker.tasks.system_task,
        worker.tasks.system_upkeep,
    ],
    worker.queues.get("background-worker"): [  # type: ignore[dict-item]
        worker.tasks.background_worker_task,
    ],
}
scheduled_tasks: dict[worker.Queue, list[worker.CronJob]] = {
    worker.queues.get("system"): [  # type: ignore[dict-item]
        worker.CronJob(
            function=worker.tasks.system_upkeep,
            unique=True,
            cron="0 * * * *",
        ),
    ],
    worker.queues.get("background-worker"): [  # type: ignore[dict-item]
        worker.CronJob(
            function=worker.tasks.background_worker_task,
            unique=True,
            cron="* * * * *",
        ),
    ],
}
