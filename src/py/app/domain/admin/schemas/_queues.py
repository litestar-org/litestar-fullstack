"""Admin and user queue inspection schemas."""

from datetime import datetime
from typing import Any

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
