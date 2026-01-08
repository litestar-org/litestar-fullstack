"""Admin domain schemas."""

from app.domain.admin.schemas._audit import AuditLogEntry
from app.domain.admin.schemas._dashboard import ActivityLogEntry, DashboardStats, RecentActivity
from app.domain.admin.schemas._teams import AdminTeamDetail, AdminTeamSummary, AdminTeamUpdate
from app.domain.admin.schemas._users import AdminUserDetail, AdminUserSummary, AdminUserUpdate

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
    "RecentActivity",
)
