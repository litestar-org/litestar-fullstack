"""Admin Queue inspection and cancellation SecureController."""

from typing import ClassVar, cast
from uuid import UUID

from litestar import get, post
from litestar.di import NamedDependency
from litestar.exceptions import HTTPException, NotFoundException
from litestar_queues import QueuedTaskRecord, QueueService, TaskStatus
from litestar_security import AuthenticationPolicy, SecureController, required, requires_role

from app.domain.admin.schemas import (
    QueueTaskCancelResponse,
    QueueTaskListResponse,
    QueueTaskSummary,
)

_VALID_TASK_STATUSES = frozenset({"pending", "scheduled", "running", "completed", "failed", "cancelled", "expired"})


def serialize_task_record(record: QueuedTaskRecord) -> QueueTaskSummary:
    """Convert a ``litestar-queues`` task record into a camelized API summary."""
    return QueueTaskSummary(
        task_id=str(record.id),
        task_name=record.task_name,
        queue=record.queue,
        status=str(record.status),
        retry_count=record.retry_count,
        max_retries=record.max_retries,
        created_at=record.created_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
        error=record.error,
        metadata=dict(record.metadata or {}),
    )


class AdminQueueController(SecureController):
    """Superuser queue monitoring and task cancellation endpoints."""

    path = "/api/admin/queues"
    tags = ["Admin"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    guards = [requires_role("superuser")]

    @get(operation_id="AdminListQueueTasks", path="/tasks")
    async def list_tasks(
        self,
        queue_service: NamedDependency[QueueService],
        status: str | None = None,
        queue: str | None = None,
        task_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> QueueTaskListResponse:
        """List queued, running, and completed background tasks."""
        resolved_status: TaskStatus | None = None
        if status is not None:
            if status not in _VALID_TASK_STATUSES:
                raise HTTPException(status_code=400, detail=f"Invalid task status: {status}")
            resolved_status = cast("TaskStatus", status)

        page = await queue_service.list_tasks(
            status=resolved_status,
            queue=queue,
            task_name=task_name,
            limit=limit,
            offset=offset,
        )
        return QueueTaskListResponse(
            items=[serialize_task_record(item) for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )

    @post(operation_id="AdminCancelQueueTask", path="/tasks/{task_id:str}/cancel")
    async def cancel_task(
        self,
        queue_service: NamedDependency[QueueService],
        task_id: str,
        include_running: bool = True,
    ) -> QueueTaskCancelResponse:
        """Cancel a queued or running background task by ID."""
        try:
            parsed_id = UUID(task_id)
        except ValueError as exc:
            raise NotFoundException(detail="Queue task not found") from exc

        existing = await queue_service.get_task(parsed_id)
        if existing is None:
            raise NotFoundException(detail="Queue task not found")

        cancelled = await queue_service.cancel_task(parsed_id, include_running=include_running)
        return QueueTaskCancelResponse(task_id=str(parsed_id), cancelled=cancelled)
