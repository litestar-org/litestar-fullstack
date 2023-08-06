from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

from litestar import Controller, MediaType, get
from litestar.response import Response
from sqlalchemy import text

from app.contrib.saq.info import is_healthy as worker_is_healthy
from app.domain.system.dtos import SystemHealth
from app.lib import constants, log
from app.lib.cache import redis

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


__all__ = ["SystemController"]


logger = log.get_logger()

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
    async def check_system_health(self, db_session: AsyncSession) -> Response[SystemHealth]:
        """Check database available and returns app config info."""
        try:
            await db_session.execute(text("select 1"))
            db_ping = True
        except ConnectionRefusedError:
            db_ping = False

        db_status = "online" if db_ping else "offline"
        cache_ping = await redis.ping()
        cache_status = "online" if cache_ping else "offline"
        worker_ping = await worker_is_healthy()
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
