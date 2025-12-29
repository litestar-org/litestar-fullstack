"""Admin Audit Log Controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import FieldNameType
from litestar import Controller, get
from litestar.params import Dependency

from app.db import models as m
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.schemas import AuditLogEntry
from app.domain.admin.services import AuditLogService
from app.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from litestar import Request
    from litestar.security.jwt import Token

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination

    from app.domain.admin.services import AuditLogService


class AuditController(Controller):
    """Admin audit log endpoints."""

    tags = ["Admin"]
    path = "/api/admin/audit"
    guards = [requires_superuser]
    dependencies = create_service_dependencies(
        AuditLogService,
        key="audit_service",
        filters={
            "id_filter": UUID,
            "search": "actor_email,action,target_label",
            "in_fields": {
                "action",
                "target_type",
                "target_id",
                FieldNameType(name="actor_id", type_hint=UUID),
            },
            "pagination_type": "limit_offset",
            "pagination_size": 50,
            "created_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    )

    @get(operation_id="AdminListAuditLogs", path="/")
    async def list_logs(
        self,
        request: Request[m.User, Token, Any],
        audit_service: AuditLogService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[AuditLogEntry]:
        """List audit logs with filtering and pagination."""
        results, total = await audit_service.list_and_count(*filters)
        return audit_service.to_schema(
            data=results,
            total=total,
            filters=filters,
            schema_type=AuditLogEntry,
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
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[AuditLogEntry]:
        """Get audit logs for a specific user."""
        filters.append(m.AuditLog.actor_id == user_id)
        results, total = await audit_service.list_and_count(*filters)
        return audit_service.to_schema(
            data=results,
            total=total,
            filters=filters,
            schema_type=AuditLogEntry,
        )

    @get(operation_id="AdminGetTargetAuditLogs", path="/target/{target_type:str}/{target_id:str}")
    async def get_target_logs(
        self,
        request: Request[m.User, Token, Any],
        audit_service: AuditLogService,
        target_type: str,
        target_id: str,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[AuditLogEntry]:
        """Get audit logs for a specific target."""
        filters.append(m.AuditLog.target_type == target_type)
        filters.append(m.AuditLog.target_id == target_id)
        results, total = await audit_service.list_and_count(*filters)
        return audit_service.to_schema(
            data=results,
            total=total,
            filters=filters,
            schema_type=AuditLogEntry,
        )
