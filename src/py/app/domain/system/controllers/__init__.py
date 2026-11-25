"""System domain controllers."""

from app.domain.system.controllers._queue import UserQueueController
from app.domain.system.controllers._system import SystemController

__all__ = (
    "SystemController",
    "UserQueueController",
)
