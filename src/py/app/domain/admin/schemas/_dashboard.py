"""Dashboard-related admin schemas."""

from datetime import datetime
from uuid import UUID

from app.lib.schema import CamelizedBaseStruct


class DashboardStats(CamelizedBaseStruct):
    """System statistics for admin dashboard."""

    total_users: int
    active_users: int
    verified_users: int
    total_teams: int
    new_users_today: int
    new_users_week: int
    events_today: int


class ActivityLogEntry(CamelizedBaseStruct, kw_only=True):
    """Single activity log entry for dashboard."""

    id: UUID
    action: str
    created_at: datetime
    actor_email: str | None = None
    target_label: str | None = None
    ip_address: str | None = None


class RecentActivity(CamelizedBaseStruct):
    """Recent activity for dashboard."""

    activities: list[ActivityLogEntry]
    total: int
