"""Audit log database service using AA 1.13 inferred default repository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar import service
from advanced_alchemy.filters import LimitOffsetFilter, OrderByFilter

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID

    from litestar import Request


class AuditLogService(service.SQLAlchemyAsyncRepositoryService[m.AuditLog]):
    """Service for recording and querying application audit log entries."""

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
        """Create and persist a new audit log entry."""
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
            },
            auto_commit=True,
        )

    async def count_recent_actions(
        self,
        *,
        action: str,
        actor_id: UUID,
        window_minutes: int,
    ) -> int:
        """Count recent actions for an actor within a rolling window."""
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
        """Return recent audit activity for a specific actor."""
        results = await self.get_many(
            LimitOffsetFilter(limit=limit, offset=0),
            OrderByFilter(field_name="created_at", sort_order="desc"),
            m.AuditLog.actor_id == user_id,
        )
        return list(results)
