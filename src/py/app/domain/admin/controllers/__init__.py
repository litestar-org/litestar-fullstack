"""Admin domain controllers."""

from app.domain.admin.controllers._audit import AuditController
from app.domain.admin.controllers._dashboard import DashboardController
from app.domain.admin.controllers._queue import AdminQueueController
from app.domain.admin.controllers._team import AdminTeamsController
from app.domain.admin.controllers._user import AdminUsersController

__all__ = (
    "AdminQueueController",
    "AdminTeamsController",
    "AdminUsersController",
    "AuditController",
    "DashboardController",
)
