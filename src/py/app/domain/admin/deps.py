"""Admin domain Advanced Alchemy filter sets and service providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import (
    FilterConfig,
    create_filter_dependencies,
    create_service_provider,
)
from advanced_alchemy.filters import FilterSet

from app.db import models as m
from app.domain.admin.services import AuditLogService, DashboardQueryService

if TYPE_CHECKING:
    from collections.abc import Collection


class AuditFilterSet(FilterSet[m.AuditLog]):
    """Typed filter set for querying audit logs."""

    model_type: ClassVar[type[m.AuditLog]] = m.AuditLog
    search_fields: ClassVar[Collection[str]] = ("actor_email", "action", "target_label")
    sort_fields: ClassVar[Collection[str]] = ("created_at", "action", "actor_email")
    config: ClassVar[FilterConfig] = {
        "id_filter": UUID,
        "pagination_type": "limit_offset",
        "pagination_size": 50,
        "created_at": True,
        "sort_field": "created_at",
        "sort_order": "desc",
    }


provide_audit_log_service = create_service_provider(
    AuditLogService,
    error_messages={"integrity": "Audit log operation failed."},
)


provide_dashboard_query_service = create_service_provider(DashboardQueryService)


__all__ = (
    "AuditFilterSet",
    "create_filter_dependencies",
    "provide_audit_log_service",
    "provide_dashboard_query_service",
)
