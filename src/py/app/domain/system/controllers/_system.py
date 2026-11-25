"""System health and public authentication configuration controller."""

from typing import Literal

import structlog
from litestar import MediaType, get
from litestar.di import NamedDependency
from litestar.response import Response
from litestar_queues import QueueService
from litestar_security import CSRF_REQUIRED_OPT_KEY, PublicController
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.system import schemas as s
from app.lib.settings import get_settings

logger = structlog.get_logger(__name__)


class SystemController(PublicController):
    """Public system health and frontend authentication configuration endpoints."""

    path = ""
    tags = ["System"]
    dependencies = {}

    @get(
        operation_id="SystemHealth",
        name="system:health",
        path="/health",
        summary="Health Check",
        mcp_resource="system_health",
    )
    async def check_system_health(
        self,
        db_session: AsyncSession,
        queue_service: NamedDependency[QueueService],
    ) -> Response[s.SystemHealth]:
        """Check database and queue backend health, returning HTTP 503 when degraded.

        Returns:
            JSON health response with HTTP 200 when healthy or HTTP 503 when degraded.
        """
        database_status = await self._probe_database(db_session)
        queue_status = await self._probe_queue(queue_service)
        healthy = database_status == "online" and queue_status == "online"
        if healthy:
            await logger.adebug("System health ok", database_status=database_status, queue_status=queue_status)
        else:
            await logger.awarning("System health degraded", database_status=database_status, queue_status=queue_status)

        return Response(
            content=s.SystemHealth(
                app=get_settings().app.NAME,
                database_status=database_status,
                queue_status=queue_status,
            ),
            status_code=200 if healthy else 503,
            media_type=MediaType.JSON,
        )

    @get(
        operation_id="PublicAuthConfig",
        name="system:auth-config",
        path="/api/config/auth",
        summary="Get Public Authentication Configuration",
        opt={CSRF_REQUIRED_OPT_KEY: True},
    )
    async def get_auth_config(self) -> s.PublicAuthConfig:
        """Return enabled OAuth providers, authentication capability flags, and the registration verification policy."""
        settings = get_settings()
        return s.PublicAuthConfig(
            github_enabled=settings.app.github_oauth_enabled,
            passkeys_enabled=True,
            mfa_enabled=True,
            email_verification_required=settings.security.REGISTRATION_REQUIRE_VERIFICATION,
        )

    @staticmethod
    async def _probe_database(db_session: AsyncSession) -> Literal["online", "offline"]:
        try:
            await db_session.execute(text("select 1"))
        except SQLAlchemyError:
            return "offline"
        return "online"

    @staticmethod
    async def _probe_queue(queue_service: QueueService) -> Literal["online", "offline"]:
        try:
            await queue_service.list_tasks(limit=1)
        except Exception:  # noqa: BLE001
            return "offline"
        return "online"
