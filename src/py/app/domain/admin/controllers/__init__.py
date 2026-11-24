"""Admin domain controllers."""

from app.domain.admin.controllers._audit import AuditController
from app.domain.admin.controllers._dashboard import DashboardController
from app.domain.admin.controllers._queues import AdminQueueController
from app.domain.admin.controllers._teams import AdminTeamsController
from app.domain.admin.controllers._users import AdminUsersController

__all__ = (
    "AdminQueueController",
    "AdminTeamsController",
    "AdminUsersController",
    "AuditController",
    "DashboardController",
)
