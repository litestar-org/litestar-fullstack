"""Admin user schemas."""

from datetime import date, datetime
from uuid import UUID

import msgspec

from app.lib.schema import CamelizedBaseStruct


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


class AdminUserUpdate(msgspec.Struct, gc=False, omit_defaults=True):
    """Update payload for admin user management."""

    name: str | None | msgspec.UnsetType = msgspec.UNSET
    username: str | None | msgspec.UnsetType = msgspec.UNSET
    phone: str | None | msgspec.UnsetType = msgspec.UNSET
    is_active: bool | msgspec.UnsetType = msgspec.UNSET
    is_superuser: bool | msgspec.UnsetType = msgspec.UNSET
    is_verified: bool | msgspec.UnsetType = msgspec.UNSET
