from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

import structlog
from litestar import Controller, MediaType, get
from litestar.response import Response
from sqlalchemy import text

from app import schemas as s

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()
OnlineOffline = TypeVar("OnlineOffline", bound=Literal["online", "offline"])


class SystemController(Controller):
    tags = ["System"]

    @get(
        operation_id="SystemHealth",
        name="system:health",
        path="/health",
        summary="Health Check",
    )
    async def check_system_health(self, db_session: AsyncSession) -> Response[s.SystemHealth]:
        """Check database available and returns app config info.

        Args:
            db_session: The database session.

        Returns:
            The response object.
        """
        db_status: Literal["online", "offline"]
        try:
            await db_session.execute(text("select 1"))
            db_status = "online"
        except ConnectionRefusedError:
            db_status = "offline"

        healthy = db_status == "online"
        if healthy:
            await logger.adebug(
                "System Health",
                database_status=db_status,
            )
        else:
            await logger.awarn(
                "System Health Check",
                database_status=db_status,
            )

        return Response(
            content=s.SystemHealth(database_status=db_status),
            status_code=200 if healthy else 500,
            media_type=MediaType.JSON,
        )
