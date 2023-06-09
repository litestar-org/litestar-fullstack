"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from litestar.contrib.jwt import OAuth2Login
from litestar.contrib.repository.abc import FilterTypes
from litestar.pagination import OffsetPagination
from pydantic import UUID4, EmailStr
from saq.types import QueueInfo

from app.domain.accounts.models import User
from app.lib import settings, worker
from app.lib.service.generic import Service
from app.lib.worker.controllers import WorkerController

from . import accounts, analytics, openapi, plugins, security, system, tags, teams, urls, web

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from litestar.types import ControllerRouterHandler


routes: list[ControllerRouterHandler] = [
    accounts.controllers.AccessController,
    accounts.controllers.AccountController,
    teams.controllers.TeamController,
    # teams.controllers.TeamInvitationController,
    # teams.controllers.TeamMemberController,
    analytics.controllers.StatsController,
    tags.controllers.TagController,
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
    "tags",
    "security",
    "routes",
    "openapi",
    "analytics",
    "plugins",
    "signature_namespace",
]
tasks: dict[worker.Queue, list[worker.WorkerFunction]] = {
    worker.queues.get("system-tasks"): [  # type: ignore[dict-item]
        worker.tasks.system_task,
        worker.tasks.system_upkeep,
    ],
    worker.queues.get("background-tasks"): [  # type: ignore[dict-item]
        worker.tasks.background_worker_task,
    ],
}
scheduled_tasks: dict[worker.Queue, list[worker.CronJob]] = {
    worker.queues.get("system-tasks"): [  # type: ignore[dict-item]
        worker.CronJob(function=worker.tasks.system_upkeep, unique=True, cron="0 * * * *", timeout=500),
    ],
    worker.queues.get("background-tasks"): [  # type: ignore[dict-item]
        worker.CronJob(function=worker.tasks.background_worker_task, unique=True, cron="* * * * *", timeout=300),
    ],
}


signature_namespace: Mapping[str, Any] = {
    "Service": Service,
    "FilterTypes": FilterTypes,
    "UUID4": UUID4,
    "UUID": UUID,
    "EmailStr": EmailStr,
    "User": User,
    "OAuth2Login": OAuth2Login,
    "OffsetPagination": OffsetPagination,
    "UserService": accounts.services.UserService,
    "TeamService": teams.services.TeamService,
    "TagService": tags.services.TagService,
    "TeamInvitationService": teams.services.TeamInvitationService,
    "TeamMemberService": teams.services.TeamMemberService,
    "Queue": worker.Queue,
    "QueueInfo": QueueInfo,
    "Job": worker.Job,
}
