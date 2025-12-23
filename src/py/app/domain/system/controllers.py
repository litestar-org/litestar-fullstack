"""System domain controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

import structlog
from litestar import Controller, MediaType, get
from litestar.di import Provide
from litestar.response import Response
from sqlalchemy import text

from app.domain.system import schemas as s
from app.lib.settings import provide_app_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.lib.settings import AppSettings

logger = structlog.get_logger()
OnlineOffline = TypeVar("OnlineOffline", bound=Literal["online", "offline"])


class SystemController(Controller):
    """System health and configuration."""

    tags = ["System"]
    dependencies = {"settings": Provide(provide_app_settings, sync_to_thread=False)}

    @get(operation_id="SystemHealth", name="system:health", path="/health", summary="Health Check")
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

    @get(
        operation_id="OAuthConfig",
        name="system:oauth-config",
        path="/api/config/oauth",
        summary="Get OAuth Configuration",
    )
    async def get_oauth_config(self, settings: AppSettings) -> s.OAuthConfig:
        """Get OAuth provider configuration for frontend.

        Args:
            settings: Application settings.

        Returns:
            OAuth configuration indicating which providers are enabled.
        """
        return s.OAuthConfig(google_enabled=settings.google_oauth_enabled, github_enabled=settings.github_oauth_enabled)
