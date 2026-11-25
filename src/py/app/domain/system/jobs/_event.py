"""Payload of the events the queue publishes about its tasks."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from app.lib.schema import CamelizedBaseStruct


class QueueTaskEventPayload(CamelizedBaseStruct):
    """Typed AsyncAPI payload emitted on the ``queue_events`` channel."""

    task_id: str
    task_name: str
    queue: str
    status: str
    timestamp: datetime
    progress: int | None = None
    total: int | None = None
    message: str | None = None
