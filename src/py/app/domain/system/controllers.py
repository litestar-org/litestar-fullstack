"""System health, public auth configuration, and user-scoped queue controllers."""

from typing import Annotated, ClassVar, Literal
from uuid import UUID

import structlog
from litestar import MediaType, get, post
from litestar.di import NamedDependency
from litestar.params import Parameter
from litestar.response import Response
from litestar_queues import QueuedTaskRecord, QueueService
from litestar_security import (
    CSRF_REQUIRED_OPT_KEY,
    AuthenticationPolicy,
    CurrentUser,
    PublicController,
    SecureController,
    any_of,
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models as m
from app.domain.accounts.security import requires_team_role
from app.domain.admin.controllers._queues import serialize_task_record
from app.domain.admin.schemas import QueueTaskListResponse, QueueTaskSummary
from app.domain.system import schemas as s
from app.domain.system.jobs import export_team_summary
from app.lib.settings import get_settings

logger = structlog.get_logger(__name__)

_OWNED_TASK_SCAN_LIMIT = 1000


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
        app_settings = get_settings().app
        db_status: Literal["online", "offline"]
        try:
            await db_session.execute(text("select 1"))
            db_status = "online"
        except SQLAlchemyError:
            db_status = "offline"

        queue_status: Literal["online", "offline"]
        try:
            await queue_service.list_tasks(limit=1)
            queue_status = "online"
        except Exception:  # noqa: BLE001
            queue_status = "offline"

        healthy = db_status == "online" and queue_status == "online"
        if healthy:
            await logger.adebug("System health ok", database_status=db_status, queue_status=queue_status)
        else:
            await logger.awarning("System health degraded", database_status=db_status, queue_status=queue_status)

        return Response(
            content=s.SystemHealth(
                app=app_settings.NAME,
                database_status=db_status,
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


class UserQueueController(SecureController):
    """User-scoped queue task inspection and safe team report enqueuing."""

    path = "/api/queues"
    tags = ["Queues"]
    auth: ClassVar[AuthenticationPolicy] = any_of("session", "api-key")

    @get(
        operation_id="ListMyQueueTasks",
        path="/tasks",
        mcp_tool="list_my_tasks",
        mcp_description="List recent background queue tasks initiated by the current user.",
    )
    async def list_my_tasks(
        self,
        queue_service: NamedDependency[QueueService],
        current_user: CurrentUser[m.User],
        limit: Annotated[int, Parameter(ge=1, le=100, description="Maximum number of tasks to return.")] = 25,
        offset: Annotated[int, Parameter(ge=0, description="Pagination offset.")] = 0,
    ) -> QueueTaskListResponse:
        """List the authenticated user's tasks among the most recent report tasks.

        Returns:
            Paginated queue task summaries initiated by the current user.
        """
        owner_id = str(current_user.id)
        owned: list[QueuedTaskRecord] = []
        batch_size = 200
        scan_offset = 0
        while scan_offset < _OWNED_TASK_SCAN_LIMIT:
            page = await queue_service.list_tasks(queue="reports", limit=batch_size, offset=scan_offset)
            owned.extend(item for item in page.items if (item.metadata or {}).get("requested_by_id") == owner_id)
            scan_offset += len(page.items)
            if len(page.items) < batch_size or scan_offset >= page.total:
                break
        sliced = owned[offset : offset + limit]
        return QueueTaskListResponse(
            items=[serialize_task_record(item) for item in sliced],
            total=len(owned),
            limit=limit,
            offset=offset,
        )

    @post(
        operation_id="EnqueueTeamSummaryReport",
        path="/reports/team-summary/{team_id:uuid}",
        guards=[requires_team_role("member")],
        mcp_tool="enqueue_team_report",
        mcp_description="Enqueue an asynchronous team summary report task for a team you belong to.",
    )
    async def enqueue_team_report(
        self,
        queue_service: NamedDependency[QueueService],
        current_user: CurrentUser[m.User],
        team_id: Annotated[UUID, Parameter(title="Team ID", description="Target team UUID.")],
    ) -> QueueTaskSummary:
        """Enqueue a background team summary report task for a team the user belongs to.

        Returns:
            Summary of the enqueued report task.
        """
        task_result = await queue_service.enqueue(
            export_team_summary,
            team_id=str(team_id),
            requested_by_id=str(current_user.id),
            metadata={"requested_by_id": str(current_user.id), "team_id": str(team_id)},
        )
        if task_result.record is not None:
            return serialize_task_record(task_result.record)
        return QueueTaskSummary(
            task_id=str(task_result.id),
            task_name=task_result.task_name,
            queue="reports",
            status=str(task_result.status),
            metadata={"requested_by_id": str(current_user.id), "team_id": str(team_id)},
        )
