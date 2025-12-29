"""Audit log service for tracking system events."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from litestar.plugins.sqlalchemy import repository, service

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
        # Extract from request if provided
        if request is not None:
            if ip_address is None:
                ip_address = request.client.host if request.client else None
            if user_agent is None:
                user_agent = request.headers.get("user-agent")

        log_entry = m.AuditLog.create_log(
            action=action,
            actor_id=actor_id,
            actor_email=actor_email,
            target_type=target_type,
            target_id=target_id,
            target_label=target_label,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.create(log_entry.to_dict())

    async def get_user_activity(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[m.AuditLog]:
        """Get activity log for a specific user.

        Args:
            user_id: The user's ID
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of audit log entries
        """
        results = await self.list(
            m.AuditLog.actor_id == user_id,
            order_by=[m.AuditLog.created_at.desc()],
            limit=limit,
            offset=offset,
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

    async def get_target_history(
        self,
        target_type: str,
        target_id: str,
        limit: int = 50,
    ) -> list[m.AuditLog]:
        """Get audit history for a specific entity.

        Args:
            target_type: Type of entity (e.g., 'user', 'team')
            target_id: ID of the entity
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries for the entity
        """
        results = await self.list(
            m.AuditLog.target_type == target_type,
            m.AuditLog.target_id == target_id,
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

        # Get counts by action type
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


# Common audit action helpers


async def log_user_action(
    service: AuditLogService,
    action: str,
    actor: m.User | None,
    target_user: m.User | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> m.AuditLog:
    """Log a user-related action.

    Args:
        service: Audit log service
        action: Action name (e.g., 'user.created', 'user.updated')
        actor: The user performing the action
        target_user: The user being acted upon
        details: Additional details
        ip_address: Request IP
        user_agent: Request user agent

    Returns:
        Created audit log entry
    """
    return await service.log_action(
        action=action,
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        target_type="user" if target_user else None,
        target_id=str(target_user.id) if target_user else None,
        target_label=target_user.email if target_user else None,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_auth_event(
    service: AuditLogService,
    action: str,
    user: m.User | None,
    success: bool = True,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> m.AuditLog:
    """Log an authentication event.

    Args:
        service: Audit log service
        action: Action name (e.g., 'login.success', 'login.failed', 'logout')
        user: The user involved
        success: Whether the action was successful
        details: Additional details
        ip_address: Request IP
        user_agent: Request user agent

    Returns:
        Created audit log entry
    """
    event_details = details or {}
    event_details["success"] = success

    return await service.log_action(
        action=action,
        actor_id=user.id if user else None,
        actor_email=user.email if user else None,
        details=event_details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
