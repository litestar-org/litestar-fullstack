"""Admin Audit Log Controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, cast
from uuid import UUID

from litestar import Controller, get
from litestar.params import Dependency, Parameter

from app.db import models as m
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.schemas import AuditLogEntry
from app.domain.admin.services import AuditLogService
from app.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from datetime import datetime

    from advanced_alchemy.extensions.litestar.providers import FilterConfig
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination


class AuditController(Controller):
    """Admin audit log endpoints."""

    tags = ["Admin"]
    path = "/api/admin/audit"
    guards = [requires_superuser]
    dependencies = create_service_dependencies(
        AuditLogService,
        key="audit_service",
        filters=cast(
            "FilterConfig",
            {
                "id_filter": UUID,
                "search": "actor_email,action,target_label",
                "in_fields": {
                    "action",
                    "target_type",
                    "target_id",
                    "actor_id",
                },
                "pagination_type": "limit_offset",
                "pagination_size": 50,
                "created_at": True,
                "sort_field": "created_at",
                "sort_order": "desc",
            },
        ),
    )

    @get(operation_id="AdminListAuditLogs", path="/")
    async def list_logs(
        self,
        audit_service: AuditLogService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
        action: str | None = Parameter(query="action", required=False),
        end_date: datetime | None = Parameter(query="end_date", required=False),  # noqa: B008
    ) -> OffsetPagination[AuditLogEntry]:
        """List audit logs with filtering and pagination.

        Args:
            audit_service: Audit log service
            filters: Filter and pagination parameters
            action: Optional action filter
            end_date: Optional upper bound for created_at

        Returns:
            Paginated audit log list
        """
        conditions: list[Any] = []
        if action:
            conditions.append(m.AuditLog.action == action)
        if end_date:
            conditions.append(m.AuditLog.created_at <= end_date)
        results, total = await audit_service.list_and_count(*filters, *conditions)
        return audit_service.to_schema(
            data=results,
            total=total,
            filters=filters,
            schema_type=AuditLogEntry,
        )

    @get(operation_id="AdminGetAuditLog", path="/{log_id:uuid}")
    async def get_log(
        self,
        audit_service: AuditLogService,
        log_id: UUID,
    ) -> AuditLogEntry:
        """Get a specific audit log entry.

        Args:
            audit_service: Audit log service
            log_id: ID of audit log to retrieve

        Returns:
            Audit log entry
        """
        log = await audit_service.get(log_id)
        return audit_service.to_schema(log, schema_type=AuditLogEntry)

    @get(operation_id="AdminGetUserAuditLogs", path="/user/{user_id:uuid}")
    async def get_user_logs(
        self,
        audit_service: AuditLogService,
        user_id: UUID,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
        action: str | None = Parameter(query="action", required=False),
        end_date: datetime | None = Parameter(query="end_date", required=False),  # noqa: B008
    ) -> OffsetPagination[AuditLogEntry]:
        """Get audit logs for a specific user."""
        conditions: list[Any] = [m.AuditLog.actor_id == user_id]
        if action:
            conditions.append(m.AuditLog.action == action)
        if end_date:
            conditions.append(m.AuditLog.created_at <= end_date)
        results, total = await audit_service.list_and_count(
            *filters,
            *conditions,
        )
        return audit_service.to_schema(
            data=results,
            total=total,
            filters=filters,
            schema_type=AuditLogEntry,
        )

    @get(operation_id="AdminGetTargetAuditLogs", path="/target/{target_type:str}/{target_id:str}")
    async def get_target_logs(
        self,
        audit_service: AuditLogService,
        target_type: str,
        target_id: str,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
        action: str | None = Parameter(query="action", required=False),
        end_date: datetime | None = Parameter(query="end_date", required=False),  # noqa: B008
    ) -> OffsetPagination[AuditLogEntry]:
        """Get audit logs for a specific target."""
        conditions = [
            m.AuditLog.target_type == target_type,
            m.AuditLog.target_id == target_id,
        ]
        if action:
            conditions.append(m.AuditLog.action == action)
        if end_date:
            conditions.append(m.AuditLog.created_at <= end_date)
        results, total = await audit_service.list_and_count(*filters, *conditions)
        return audit_service.to_schema(
            data=results,
            total=total,
            filters=filters,
            schema_type=AuditLogEntry,
        )
