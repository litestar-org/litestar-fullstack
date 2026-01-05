"""Audit log service for tracking system events."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID

    from litestar import Request


class AuditLogService(service.SQLAlchemyAsyncRepositoryService[m.AuditLog]):
    """Service for audit log operations."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.AuditLog]):
        """AuditLog SQLAlchemy Repository."""

        model_type = m.AuditLog

    repository_type = Repo

    async def log_action(
        self,
        action: str,
        actor_id: UUID | None = None,
        actor_email: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        target_label: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request: Request[Any, Any, Any] | None = None,
    ) -> m.AuditLog:
        """Create a new audit log entry.

        Args:
            action: The action performed (e.g., 'user.created', 'login.failed')
            actor_id: ID of the user performing the action
            actor_email: Email of the actor
            target_type: Type of target entity (e.g., 'user', 'team')
            target_id: ID of target entity
            target_label: Human-readable label for target
            details: Additional context as JSON
            ip_address: Request IP address (extracted from request if not provided)
            user_agent: Request user agent (extracted from request if not provided)
            request: Optional Litestar request to extract ip_address and user_agent from

        Returns:
            Created AuditLog instance
        """

        if request is not None:
            if ip_address is None:
                ip_address = request.client.host if request.client else None
            if user_agent is None:
                user_agent = request.headers.get("user-agent")

        return await self.create(
            {
                "action": action,
                "actor_id": actor_id,
                "actor_email": actor_email,
                "target_type": target_type,
                "target_id": target_id,
                "target_label": target_label,
                "details": details,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
        )

    async def count_recent_actions(
        self,
        *,
        action: str,
        actor_id: UUID,
        window_minutes: int,
    ) -> int:
        """Count recent actions for an actor within a rolling window.

        Args:
            action: Action name to count.
            actor_id: Actor ID to filter by.
            window_minutes: Window size in minutes.

        Returns:
            Number of matching actions within the time window.
        """
        cutoff_time = datetime.now(UTC) - timedelta(minutes=window_minutes)
        return await self.count(
            m.AuditLog.action == action,
            m.AuditLog.actor_id == actor_id,
            m.AuditLog.created_at >= cutoff_time,
        )

    async def log_admin_user_update(
        self,
        *,
        actor_id: UUID,
        actor_email: str | None,
        user_id: UUID,
        user_email: str,
        changes: list[str],
        request: Request[Any, Any, Any] | None = None,
    ) -> m.AuditLog:
        """Log an admin user update event."""
        return await self.log_action(
            action="admin.user.update",
            actor_id=actor_id,
            actor_email=actor_email,
            target_type="user",
            target_id=str(user_id),
            target_label=user_email,
            details={"changes": changes},
            request=request,
        )

    async def log_admin_user_delete(
        self,
        *,
        actor_id: UUID,
        actor_email: str | None,
        user_id: UUID,
        user_email: str,
        request: Request[Any, Any, Any] | None = None,
    ) -> m.AuditLog:
        """Log an admin user deletion event."""
        return await self.log_action(
            action="admin.user.delete",
            actor_id=actor_id,
            actor_email=actor_email,
            target_type="user",
            target_id=str(user_id),
            target_label=user_email,
            request=request,
        )

    async def log_admin_team_update(
        self,
        *,
        actor_id: UUID,
        actor_email: str | None,
        team_id: UUID,
        team_name: str,
        changes: list[str],
        request: Request[Any, Any, Any] | None = None,
    ) -> m.AuditLog:
        """Log an admin team update event."""
        return await self.log_action(
            action="admin.team.update",
            actor_id=actor_id,
            actor_email=actor_email,
            target_type="team",
            target_id=str(team_id),
            target_label=team_name,
            details={"changes": changes},
            request=request,
        )

    async def log_admin_team_delete(
        self,
        *,
        actor_id: UUID,
        actor_email: str | None,
        team_id: UUID,
        team_name: str,
        request: Request[Any, Any, Any] | None = None,
    ) -> m.AuditLog:
        """Log an admin team deletion event."""
        return await self.log_action(
            action="admin.team.delete",
            actor_id=actor_id,
            actor_email=actor_email,
            target_type="team",
            target_id=str(team_id),
            target_label=team_name,
            request=request,
        )

    async def get_user_activity(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> list[m.AuditLog]:
        """Get recent audit activity for a specific user.

        Args:
            user_id: User ID to filter by.
            limit: Maximum number of entries to return.

        Returns:
            List of audit log entries for the user.
        """
        results = await self.list(
            m.AuditLog.actor_id == user_id,
            order_by=[m.AuditLog.created_at.desc()],
            limit=limit,
        )
        return list(results)

    async def get_recent_activity(
        self,
        hours: int = 24,
        limit: int = 100,
        action_filter: str | None = None,
    ) -> list[m.AuditLog]:
        """Get recent system activity.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of entries to return
            action_filter: Optional action prefix to filter by (e.g., 'user.')

        Returns:
            List of recent audit log entries
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        conditions = [m.AuditLog.created_at >= cutoff_time]
        if action_filter:
            conditions.append(m.AuditLog.action.startswith(action_filter))

        results = await self.list(
            *conditions,
            order_by=[m.AuditLog.created_at.desc()],
            limit=limit,
        )
        return list(results)

    async def get_stats(self, hours: int = 24) -> dict[str, Any]:
        """Get audit log statistics.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with statistics
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        recent_logs = await self.list(m.AuditLog.created_at >= cutoff_time)

        action_counts: dict[str, int] = {}
        for log in recent_logs:
            action_prefix = log.action.split(".")[0]
            action_counts[action_prefix] = action_counts.get(action_prefix, 0) + 1

        return {
            "total_events": len(recent_logs),
            "action_counts": action_counts,
            "period_hours": hours,
        }
