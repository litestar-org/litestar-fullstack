"""Admin Audit Log Controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar import Controller, get
from litestar.di import Provide

from app.db import models as m
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.dependencies import provide_audit_log_service
from app.domain.admin.schemas import AuditLogEntry, AuditLogList

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from litestar import Request
    from litestar.security.jwt import Token

    from app.domain.admin.services import AuditLogService


class AuditController(Controller):
    """Admin audit log endpoints."""

    tags = ["Admin"]
    path = "/api/admin/audit"
    guards = [requires_superuser]
    dependencies = {
        "audit_service": Provide(provide_audit_log_service),
    }

    @get(operation_id="AdminListAuditLogs", path="/")
    async def list_logs(
        self,
        request: Request[m.User, Token, Any],
        audit_service: AuditLogService,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        actor_id: UUID | None = None,
        target_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> AuditLogList:
        """List audit logs with filtering and pagination.

        Args:
            request: Request with authenticated superuser
            audit_service: Audit log service
            page: Page number (1-indexed)
            page_size: Items per page
            action: Filter by action type
            actor_id: Filter by actor user ID
            target_type: Filter by target type
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            Paginated audit log list
        """
        from sqlalchemy import ColumnElement, and_, select

        # Build filters
        filters: list[ColumnElement[bool]] = []
        if action:
            filters.append(m.AuditLog.action == action)
        if actor_id:
            filters.append(m.AuditLog.actor_id == actor_id)
        if target_type:
            filters.append(m.AuditLog.target_type == target_type)
        if start_date:
            filters.append(m.AuditLog.created_at >= start_date)
        if end_date:
            filters.append(m.AuditLog.created_at <= end_date)

        # Get filtered logs
        if filters:
            stmt = select(m.AuditLog).where(and_(*filters)).order_by(m.AuditLog.created_at.desc())
            all_logs = list(await audit_service.repository.session.scalars(stmt))
        else:
            all_logs = list(await audit_service.list())
            all_logs = sorted(all_logs, key=lambda x: x.created_at, reverse=True)

        total = len(all_logs)

        # Manual pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = all_logs[start:end]

        items = [
            AuditLogEntry(
                id=log.id,
                action=log.action,
                actor_id=log.actor_id,
                actor_email=log.actor_email,
                target_type=log.target_type,
                target_id=log.target_id,
                target_label=log.target_label,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in paginated_logs
        ]

        return AuditLogList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    @get(operation_id="AdminGetAuditLog", path="/{log_id:uuid}")
    async def get_log(
        self,
        request: Request[m.User, Token, Any],
        audit_service: AuditLogService,
        log_id: UUID,
    ) -> AuditLogEntry:
        """Get a specific audit log entry.

        Args:
            request: Request with authenticated superuser
            audit_service: Audit log service
            log_id: ID of audit log to retrieve

        Returns:
            Audit log entry
        """
        log = await audit_service.get(log_id)

        return AuditLogEntry(
            id=log.id,
            action=log.action,
            actor_id=log.actor_id,
            actor_email=log.actor_email,
            target_type=log.target_type,
            target_id=log.target_id,
            target_label=log.target_label,
            details=log.details,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        )

    @get(operation_id="AdminGetUserAuditLogs", path="/user/{user_id:uuid}")
    async def get_user_logs(
        self,
        request: Request[m.User, Token, Any],
        audit_service: AuditLogService,
        user_id: UUID,
        limit: int = 50,
    ) -> list[AuditLogEntry]:
        """Get audit logs for a specific user.

        Args:
            request: Request with authenticated superuser
            audit_service: Audit log service
            user_id: ID of user to get logs for
            limit: Maximum number of entries

        Returns:
            List of audit log entries
        """
        logs = await audit_service.get_user_activity(user_id=user_id, limit=limit)

        return [
            AuditLogEntry(
                id=log.id,
                action=log.action,
                actor_id=log.actor_id,
                actor_email=log.actor_email,
                target_type=log.target_type,
                target_id=log.target_id,
                target_label=log.target_label,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in logs
        ]

    @get(operation_id="AdminGetTargetAuditLogs", path="/target/{target_type:str}/{target_id:str}")
    async def get_target_logs(
        self,
        request: Request[m.User, Token, Any],
        audit_service: AuditLogService,
        target_type: str,
        target_id: str,
        limit: int = 50,
    ) -> list[AuditLogEntry]:
        """Get audit logs for a specific target.

        Args:
            request: Request with authenticated superuser
            audit_service: Audit log service
            target_type: Type of target (user, team, etc.)
            target_id: ID of target
            limit: Maximum number of entries

        Returns:
            List of audit log entries
        """
        logs = await audit_service.get_target_history(
            target_type=target_type,
            target_id=target_id,
            limit=limit,
        )

        return [
            AuditLogEntry(
                id=log.id,
                action=log.action,
                actor_id=log.actor_id,
                actor_email=log.actor_email,
                target_type=log.target_type,
                target_id=log.target_id,
                target_label=log.target_label,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in logs
        ]
