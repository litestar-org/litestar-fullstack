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
        """Execute parameterized aggregate counts for users, teams, and 24-hour audit events.

        Returns:
            Aggregated dashboard statistics snapshot.
        """
        current_time = now or datetime.now(UTC)
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        events_cutoff = current_time - timedelta(hours=24)

        user_counts_statement = select(
            func.count(m.User.id),
            func.coalesce(func.sum(case((m.User.is_active.is_(true()), 1), else_=0)), 0),
            func.coalesce(func.sum(case((m.User.is_verified.is_(true()), 1), else_=0)), 0),
            func.coalesce(func.sum(case((m.User.created_at >= today_start, 1), else_=0)), 0),
            func.coalesce(func.sum(case((m.User.created_at >= week_start, 1), else_=0)), 0),
        )
        team_count_statement = select(func.count(m.Team.id))
        event_count_statement = select(func.count(m.AuditLog.id)).where(m.AuditLog.created_at >= events_cutoff)

        with wrap_sqlalchemy_exception():
            total_users, active_users, verified_users, new_users_today, new_users_week = (
                await self.repository.session.execute(user_counts_statement)
            ).one()
            total_teams = int((await self.repository.session.scalar(team_count_statement)) or 0)
            events_today = int((await self.repository.session.scalar(event_count_statement)) or 0)

        return DashboardStats(
            total_users=int(total_users or 0),
            active_users=int(active_users or 0),
            verified_users=int(verified_users or 0),
            total_teams=total_teams,
            new_users_today=int(new_users_today or 0),
            new_users_week=int(new_users_week or 0),
            events_today=events_today,
        )
