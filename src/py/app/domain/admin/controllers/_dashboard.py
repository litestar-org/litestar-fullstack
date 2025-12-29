"""Admin Dashboard Controller."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from litestar import Controller, get
from litestar.di import Provide

from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.dependencies import provide_audit_log_service
from app.domain.admin.schemas import ActivityLogEntry, DashboardStats, RecentActivity
from app.domain.teams.dependencies import provide_teams_service

if TYPE_CHECKING:
    from litestar import Request
    from litestar.security.jwt import Token

    from app.db import models as m
    from app.domain.accounts.services import UserService
    from app.domain.admin.services import AuditLogService
    from app.domain.teams.services import TeamService


class DashboardController(Controller):
    """Admin dashboard endpoints for system statistics and activity monitoring."""

    tags = ["Admin"]
    path = "/api/admin/dashboard"
    guards = [requires_superuser]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "teams_service": Provide(provide_teams_service),
        "audit_service": Provide(provide_audit_log_service),
    }

    @get(operation_id="GetDashboardStats", path="/stats")
    async def get_stats(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        teams_service: TeamService,
        audit_service: AuditLogService,
    ) -> DashboardStats:
        """Get system statistics for admin dashboard.

        Args:
            request: Request with authenticated superuser
            users_service: User service
            teams_service: Team service
            audit_service: Audit log service

        Returns:
            Dashboard statistics
        """
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        # Get user counts
        all_users = await users_service.list()
        total_users = len(all_users)
        active_users = sum(1 for u in all_users if u.is_active)
        verified_users = sum(1 for u in all_users if u.is_verified)
        new_users_today = sum(1 for u in all_users if u.created_at >= today_start)
        new_users_week = sum(1 for u in all_users if u.created_at >= week_start)

        # Get team count
        all_teams = await teams_service.list()
        total_teams = len(all_teams)

        # Get today's events count
        audit_stats = await audit_service.get_stats(hours=24)
        events_today = audit_stats["total_events"]

        return DashboardStats(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            total_teams=total_teams,
            new_users_today=new_users_today,
            new_users_week=new_users_week,
            events_today=events_today,
        )

    @get(operation_id="GetRecentActivity", path="/activity")
    async def get_activity(
        self,
        request: Request[m.User, Token, Any],
        audit_service: AuditLogService,
        hours: int = 24,
        limit: int = 50,
    ) -> RecentActivity:
        """Get recent system activity for admin dashboard.

        Args:
            request: Request with authenticated superuser
            audit_service: Audit log service
            hours: Number of hours to look back (default 24)
            limit: Maximum number of entries (default 50)

        Returns:
            Recent activity list
        """
        recent_logs = await audit_service.get_recent_activity(hours=hours, limit=limit)

        activities = [
            ActivityLogEntry(
                id=log.id,
                action=log.action,
                actor_email=log.actor_email,
                target_label=log.target_label,
                created_at=log.created_at,
                ip_address=log.ip_address,
            )
            for log in recent_logs
        ]

        return RecentActivity(
            activities=activities,
            total=len(activities),
        )
