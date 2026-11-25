"""Admin domain schemas."""

from app.domain.admin.schemas._audit import AuditLogEntry
from app.domain.admin.schemas._dashboard import ActivityLogEntry, DashboardStats, RecentActivity
from app.domain.admin.schemas._queue import (
    QueueTaskCancelResponse,
    QueueTaskListResponse,
    QueueTaskSummary,
)
from app.domain.admin.schemas._team import AdminTeamDetail, AdminTeamSummary, AdminTeamUpdate
from app.domain.admin.schemas._user import AdminUserDetail, AdminUserSummary, AdminUserUpdate

__all__ = (
    "ActivityLogEntry",
    "AdminTeamDetail",
    "AdminTeamSummary",
    "AdminTeamUpdate",
    "AdminUserDetail",
    "AdminUserSummary",
    "AdminUserUpdate",
    "AuditLogEntry",
    "DashboardStats",
    "QueueTaskCancelResponse",
    "QueueTaskListResponse",
    "QueueTaskSummary",
    "RecentActivity",
)
