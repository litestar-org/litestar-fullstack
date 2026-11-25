"""Admin and user queue inspection schemas."""

from datetime import datetime
from typing import Any, Self

from litestar_queues import QueuedTaskRecord

from app.lib.schema import CamelizedBaseStruct


class QueueTaskSummary(CamelizedBaseStruct, kw_only=True):
    """Serialized background queue task record."""

    task_id: str
    task_name: str
    queue: str
    status: str
    retry_count: int = 0
    max_retries: int = 0
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] = {}

    @classmethod
    def from_record(cls, record: QueuedTaskRecord) -> Self:
        """Summarize a ``litestar-queues`` task record for the API.

        Returns:
            Summary of the queued task.
        """
        return cls(
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


class QueueTaskListResponse(CamelizedBaseStruct):
    """Paginated response for queue task listings."""

    items: list[QueueTaskSummary]
    total: int
    limit: int
    offset: int


class QueueTaskCancelResponse(CamelizedBaseStruct):
    """Response confirming task cancellation attempt."""

    task_id: str
    cancelled: bool
