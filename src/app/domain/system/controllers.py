from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

import structlog
from litestar import Controller, MediaType, Request, get
from litestar.response import Response
from sqlalchemy import text

from app.config import constants, settings
from app.domain.system.dtos import SystemHealth

if TYPE_CHECKING:
    from litestar_saq import TaskQueues
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()
OnlineOffline = TypeVar("OnlineOffline", bound=Literal["online", "offline"])


class SystemController(Controller):
    tags = ["System"]

    @get(
        operation_id="SystemHealth",
        name="system:health",
        path=constants.SYSTEM_HEALTH,
        media_type=MediaType.JSON,
        cache=False,
        tags=["System"],
        summary="Health Check",
        description="Execute a health check against backend components.  Returns system information including database and cache status.",
        signature_namespace={"SystemHealth": SystemHealth},
    )
    async def check_system_health(
        self,
        request: Request,
        db_session: AsyncSession,
        task_queues: TaskQueues,
    ) -> Response[SystemHealth]:
        """Check database available and returns app config info."""
        try:
            await db_session.execute(text("select 1"))
            db_ping = True
        except ConnectionRefusedError:
            db_ping = False

        db_status = "online" if db_ping else "offline"
        cache_ping = await settings.redis.get_client().ping()
        cache_status = "online" if cache_ping else "offline"
        worker_ping = bool([await queue.info() for queue in task_queues.queues.values()])
        worker_status = "online" if worker_ping else "offline"
        healthy = bool(worker_ping and cache_ping and db_ping)
        if healthy:
            await logger.adebug(
                "System Health",
                database_status=db_status,
                cache_status=cache_status,
                worker_status=worker_status,
            )
        else:
            await logger.awarn(
                "System Health Check",
                database_status=db_status,
                cache_status=cache_status,
                worker_status=worker_status,
            )

        return Response(
            content=SystemHealth(database_status=db_status, cache_status=cache_status, worker_status=worker_status),  # type: ignore
            status_code=200 if db_ping and cache_ping and worker_ping else 500,
            media_type=MediaType.JSON,
        )
