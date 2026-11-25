"""User-scoped queue task controller."""

from typing import Annotated, ClassVar
from uuid import UUID

from litestar import get, post
from litestar.di import NamedDependency
from litestar.params import Parameter
from litestar_queues import QueuedTaskRecord, QueueService
from litestar_security import AuthenticationPolicy, CurrentUser, SecureController, any_of

from app.db import models as m
from app.domain.accounts.security import requires_team_role
from app.domain.admin.schemas import QueueTaskListResponse, QueueTaskSummary
from app.domain.system.jobs import export_team_summary

_OWNED_TASK_SCAN_LIMIT = 1000
_OWNED_TASK_SCAN_BATCH_SIZE = 200


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
        owned_tasks = await self._scan_owned_report_tasks(queue_service, owner_id=str(current_user.id))
        return QueueTaskListResponse(
            items=[QueueTaskSummary.from_record(task) for task in owned_tasks[offset : offset + limit]],
            total=len(owned_tasks),
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
        report_task = await queue_service.enqueue(
            export_team_summary,
            team_id=str(team_id),
            requested_by_id=str(current_user.id),
            metadata={"requested_by_id": str(current_user.id), "team_id": str(team_id)},
        )
        if report_task.record is not None:
            return QueueTaskSummary.from_record(report_task.record)
        return QueueTaskSummary(
            task_id=str(report_task.id),
            task_name=report_task.task_name,
            queue="reports",
            status=str(report_task.status),
            metadata={"requested_by_id": str(current_user.id), "team_id": str(team_id)},
        )

    @staticmethod
    async def _scan_owned_report_tasks(queue_service: QueueService, *, owner_id: str) -> list[QueuedTaskRecord]:
        owned_tasks: list[QueuedTaskRecord] = []
        scan_offset = 0
        while scan_offset < _OWNED_TASK_SCAN_LIMIT:
            page = await queue_service.list_tasks(
                queue="reports",
                limit=_OWNED_TASK_SCAN_BATCH_SIZE,
                offset=scan_offset,
            )
            owned_tasks.extend(task for task in page.items if (task.metadata or {}).get("requested_by_id") == owner_id)
            scan_offset += len(page.items)
            if len(page.items) < _OWNED_TASK_SCAN_BATCH_SIZE or scan_offset >= page.total:
                break
        return owned_tasks
