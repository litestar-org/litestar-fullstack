"""First-party ``litestar-queues`` SQLAlchemy models bound to the shared Advanced Alchemy metadata."""

from __future__ import annotations

from litestar_queues.backends.advanced_alchemy import (
    QueueEventHistoryModel as QueueEventHistory,
)
from litestar_queues.backends.advanced_alchemy import (
    QueueMaintenanceModel as QueueMaintenance,
)
from litestar_queues.backends.advanced_alchemy import (
    QueueTaskModel as QueueTask,
)
from litestar_queues.backends.advanced_alchemy import (
    QueueTaskReservationModel as QueueTaskReservation,
)

__all__ = (
    "QueueEventHistory",
    "QueueMaintenance",
    "QueueTask",
    "QueueTaskReservation",
)
