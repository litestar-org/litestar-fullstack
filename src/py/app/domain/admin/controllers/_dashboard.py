"""Admin Dashboard SecureController."""

from datetime import UTC, datetime, timedelta
from typing import ClassVar

from advanced_alchemy.filters import LimitOffsetFilter, OrderByFilter
from litestar import get
from litestar.di import Provide
from litestar_security import AuthenticationPolicy, SecureController, required, requires_role

from app.db import models as m
from app.domain.admin.deps import provide_audit_log_service, provide_dashboard_query_service
from app.domain.admin.schemas import ActivityLogEntry, DashboardStats, RecentActivity
from app.domain.admin.services import AuditLogService, DashboardQueryService


class DashboardController(SecureController):
    """Admin dashboard endpoints for aggregate statistics and recent activity."""

    path = "/api/admin/dashboard"
    tags = ["Admin"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    guards = [requires_role("superuser")]
    dependencies = {
        "dashboard_query_service": Provide(provide_dashboard_query_service, sync_to_thread=False),
        "audit_service": Provide(provide_audit_log_service),
    }

    @get(operation_id="GetDashboardStats", path="/stats")
    async def get_stats(
        self,
        dashboard_query_service: DashboardQueryService,
    ) -> DashboardStats:
        """Return aggregate system statistics for the admin dashboard."""
        return await dashboard_query_service.get_stats()

    @get(operation_id="GetRecentActivity", path="/activity")
    async def get_activity(
        self,
        audit_service: AuditLogService,
        hours: int = 24,
        limit: int = 50,
    ) -> RecentActivity:
        """Return recent audit activity within the requested time window."""
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        results, total = await audit_service.get_many_and_count(
            LimitOffsetFilter(limit=limit, offset=0),
            OrderByFilter(field_name="created_at", sort_order="desc"),
            m.AuditLog.created_at >= cutoff_time,
        )
        items = [
            ActivityLogEntry(
                id=log.id,
                action=log.action,
                actor_email=log.actor_email,
                target_label=log.target_label,
                created_at=log.created_at,
            )
            for log in results
        ]
        return RecentActivity(activities=items, total=total)
