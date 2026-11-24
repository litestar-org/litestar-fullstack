"""Aggregate admin dashboard query service backed by ``SQLAlchemyAsyncQueryService``."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from advanced_alchemy.exceptions import wrap_sqlalchemy_exception
from advanced_alchemy.service import SQLAlchemyAsyncQueryService
from sqlalchemy import case, func, select, true

from app.db import models as m
from app.domain.admin.schemas import DashboardStats


class DashboardQueryService(SQLAlchemyAsyncQueryService):
    """Computes admin dashboard statistics via parameterized SQL aggregate queries."""

    async def get_stats(self, *, now: datetime | None = None) -> DashboardStats:
        """Execute parameterized aggregate counts for users, teams, and 24-hour audit events."""
        current = now or datetime.now(UTC)
        today_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        events_cutoff = current - timedelta(hours=24)

        user_agg_stmt = select(
            func.count(m.User.id),
            func.coalesce(func.sum(case((m.User.is_active.is_(true()), 1), else_=0)), 0),
            func.coalesce(func.sum(case((m.User.is_verified.is_(true()), 1), else_=0)), 0),
            func.coalesce(func.sum(case((m.User.created_at >= today_start, 1), else_=0)), 0),
            func.coalesce(func.sum(case((m.User.created_at >= week_start, 1), else_=0)), 0),
        )
        team_count_stmt = select(func.count(m.Team.id))
        audit_count_stmt = select(func.count(m.AuditLog.id)).where(m.AuditLog.created_at >= events_cutoff)

        with wrap_sqlalchemy_exception():
            row = (await self.repository.session.execute(user_agg_stmt)).one()
            total_teams = int((await self.repository.session.scalar(team_count_stmt)) or 0)
            events_today = int((await self.repository.session.scalar(audit_count_stmt)) or 0)

        return DashboardStats(
            total_users=int(row[0] or 0),
            active_users=int(row[1] or 0),
            verified_users=int(row[2] or 0),
            total_teams=total_teams,
            new_users_today=int(row[3] or 0),
            new_users_week=int(row[4] or 0),
            events_today=events_today,
        )
