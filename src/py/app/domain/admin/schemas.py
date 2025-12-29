"""Admin domain schemas."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

import msgspec

from app.schemas.base import CamelizedBaseStruct

__all__ = (
    "ActivityLogEntry",
    "AdminTeamDetail",
    "AdminTeamSummary",
    "AdminTeamUpdate",
    "AdminUserDetail",
    "AdminUserSummary",
    "AdminUserUpdate",
    "AuditLogEntry",
    "DashboardStats",
    "RecentActivity",
)


class DashboardStats(CamelizedBaseStruct):
    """System statistics for admin dashboard."""

    total_users: int
    active_users: int
    verified_users: int
    total_teams: int
    new_users_today: int
    new_users_week: int
    events_today: int


class ActivityLogEntry(CamelizedBaseStruct, kw_only=True):
    """Single activity log entry for dashboard."""

    id: UUID
    action: str
    created_at: datetime
    actor_email: str | None = None
    target_label: str | None = None
    ip_address: str | None = None


class RecentActivity(CamelizedBaseStruct):
    """Recent activity for dashboard."""

    activities: list[ActivityLogEntry]
    total: int


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


class AdminUserSummary(CamelizedBaseStruct, kw_only=True):
    """Summary user info for admin lists."""

    id: UUID
    email: str
    created_at: datetime
    name: str | None = None
    username: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    login_count: int = 0


class AdminUserDetail(CamelizedBaseStruct, kw_only=True):
    """Detailed user info for admin view."""

    id: UUID
    email: str
    created_at: datetime
    updated_at: datetime
    name: str | None = None
    username: str | None = None
    phone: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    verified_at: date | None = None
    joined_at: date | None = None
    login_count: int = 0
    is_two_factor_enabled: bool = False
    has_password: bool = True
    roles: list[str] = []
    teams: list[str] = []
    oauth_providers: list[str] = []


class AdminUserUpdate(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Update payload for admin user management."""

    name: str | None | msgspec.UnsetType = msgspec.UNSET
    username: str | None | msgspec.UnsetType = msgspec.UNSET
    phone: str | None | msgspec.UnsetType = msgspec.UNSET
    is_active: bool | msgspec.UnsetType = msgspec.UNSET
    is_superuser: bool | msgspec.UnsetType = msgspec.UNSET
    is_verified: bool | msgspec.UnsetType = msgspec.UNSET


class AdminTeamSummary(CamelizedBaseStruct, kw_only=True):
    """Summary team info for admin lists."""

    id: UUID
    name: str
    slug: str
    created_at: datetime
    member_count: int = 0
    is_active: bool = True


class AdminTeamDetail(CamelizedBaseStruct, kw_only=True):
    """Detailed team info for admin view."""

    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    is_active: bool = True
    member_count: int = 0
    owner_email: str | None = None


class AdminTeamUpdate(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Update payload for admin team management."""

    name: str | None | msgspec.UnsetType = msgspec.UNSET
    description: str | None | msgspec.UnsetType = msgspec.UNSET
    is_active: bool | msgspec.UnsetType = msgspec.UNSET
