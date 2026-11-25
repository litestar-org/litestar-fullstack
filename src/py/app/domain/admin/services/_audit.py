"""Audit log database service using AA 1.13 inferred default repository."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar import service

from app.db import models as m

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from uuid import UUID

    from advanced_alchemy.filters import StatementFilter
    from litestar import Request
    from sqlalchemy import ColumnElement


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
        """Create and persist a new audit log entry.

        Returns:
            The persisted ``AuditLog`` record.
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
            },
            auto_commit=True,
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
        """Log an admin user update event.

        Returns:
            The persisted ``AuditLog`` record.
        """
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
        """Log an admin user deletion event.

        Returns:
            The persisted ``AuditLog`` record.
        """
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
        """Log an admin team update event.

        Returns:
            The persisted ``AuditLog`` record.
        """
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
        """Log an admin team deletion event.

        Returns:
            The persisted ``AuditLog`` record.
        """
        return await self.log_action(
            action="admin.team.delete",
            actor_id=actor_id,
            actor_email=actor_email,
            target_type="team",
            target_id=str(team_id),
            target_label=team_name,
            request=request,
        )

    async def find_logs(
        self,
        *filters: StatementFilter | ColumnElement[bool],
        action: str | None = None,
        end_date: datetime | None = None,
    ) -> tuple[Sequence[m.AuditLog], int]:
        """Find audit logs matching ``filters``, optionally narrowed to one action and to entries up to ``end_date``.

        Returns:
            The matching audit logs and their total count before pagination.
        """
        criteria: list[ColumnElement[bool]] = []
        if action:
            criteria.append(m.AuditLog.action == action)
        if end_date:
            criteria.append(m.AuditLog.created_at <= end_date)
        return await self.get_many_and_count(*filters, *criteria)
