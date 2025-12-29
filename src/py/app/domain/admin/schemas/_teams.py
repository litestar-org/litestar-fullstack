"""Admin team schemas."""

from datetime import datetime
from uuid import UUID

import msgspec

from app.lib.schema import CamelizedBaseStruct


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
