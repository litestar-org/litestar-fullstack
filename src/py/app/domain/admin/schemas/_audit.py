"""Audit log schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.lib.schema import CamelizedBaseStruct


class AuditLogEntry(CamelizedBaseStruct, kw_only=True):
    """Detailed audit log entry."""

    id: UUID
    action: str
    created_at: datetime
    actor_id: UUID | None = None
    actor_email: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    target_label: str | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
