"""Admin Audit Log SecureController."""

from datetime import datetime
from typing import Annotated, Any, ClassVar
from uuid import UUID

from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service.pagination import OffsetPagination
from litestar import get
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar_security import AuthenticationPolicy, SecureController, required, requires_role

from app.db import models as m
from app.domain.admin.deps import AuditFilterSet, create_filter_dependencies, provide_audit_log_service
from app.domain.admin.schemas import AuditLogEntry
from app.domain.admin.services import AuditLogService


class AuditController(SecureController):
    """Superuser audit log inspection endpoints."""

    path = "/api/admin/audit"
    tags = ["Admin"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    guards = [requires_role("superuser")]
    dependencies = {
        "audit_service": Provide(provide_audit_log_service),
    } | create_filter_dependencies(AuditFilterSet)

    @get(operation_id="AdminListAuditLogs", path="/")
    async def list_logs(
        self,
        audit_service: AuditLogService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
        action: Annotated[str | None, Parameter(query="action", required=False)] = None,
        end_date: Annotated[datetime | None, Parameter(query="end_date", required=False)] = None,
    ) -> OffsetPagination[AuditLogEntry]:
        """List audit logs with filtering and pagination.

        Returns:
            Paginated audit log entries.
        """
        conditions: list[Any] = []
        if action:
            conditions.append(m.AuditLog.action == action)
        if end_date:
            conditions.append(m.AuditLog.created_at <= end_date)
        results, total = await audit_service.get_many_and_count(*filters, *conditions)
        return audit_service.to_schema(results, total, filters, schema_type=AuditLogEntry)

    @get(operation_id="AdminGetAuditLog", path="/{log_id:uuid}")
    async def get_log(
        self,
        audit_service: AuditLogService,
        log_id: UUID,
    ) -> AuditLogEntry:
        """Get a specific audit log entry by ID.

        Returns:
            The matching audit log entry.
        """
        log = await audit_service.get(log_id)
        return audit_service.to_schema(log, schema_type=AuditLogEntry)

    @get(operation_id="AdminGetUserAuditLogs", path="/user/{user_id:uuid}")
    async def get_user_logs(
        self,
        audit_service: AuditLogService,
        user_id: UUID,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
        action: Annotated[str | None, Parameter(query="action", required=False)] = None,
        end_date: Annotated[datetime | None, Parameter(query="end_date", required=False)] = None,
    ) -> OffsetPagination[AuditLogEntry]:
        """List audit logs recorded for a specific actor.

        Returns:
            Paginated audit log entries for the actor.
        """
        conditions: list[Any] = [m.AuditLog.actor_id == user_id]
        if action:
            conditions.append(m.AuditLog.action == action)
        if end_date:
            conditions.append(m.AuditLog.created_at <= end_date)
        results, total = await audit_service.get_many_and_count(*filters, *conditions)
        return audit_service.to_schema(results, total, filters, schema_type=AuditLogEntry)

    @get(operation_id="AdminGetTargetAuditLogs", path="/target/{target_type:str}/{target_id:str}")
    async def get_target_logs(
        self,
        audit_service: AuditLogService,
        target_type: str,
        target_id: str,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
        action: Annotated[str | None, Parameter(query="action", required=False)] = None,
        end_date: Annotated[datetime | None, Parameter(query="end_date", required=False)] = None,
    ) -> OffsetPagination[AuditLogEntry]:
        """List audit logs recorded for a specific target resource.

        Returns:
            Paginated audit log entries for the target resource.
        """
        conditions: list[Any] = [
            m.AuditLog.target_type == target_type,
            m.AuditLog.target_id == target_id,
        ]
        if action:
            conditions.append(m.AuditLog.action == action)
        if end_date:
            conditions.append(m.AuditLog.created_at <= end_date)
        results, total = await audit_service.get_many_and_count(*filters, *conditions)
        return audit_service.to_schema(results, total, filters, schema_type=AuditLogEntry)
