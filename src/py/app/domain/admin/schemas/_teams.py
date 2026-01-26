"""Admin team schemas."""

from datetime import datetime
from uuid import UUID

import msgspec

from app.domain.accounts.schemas import User
from app.lib.schema import CamelizedBaseStruct


class AdminTeamMember(CamelizedBaseStruct):
    """Team member info for admin view."""

    user: User
    role: str
    is_owner: bool


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
    members: list[AdminTeamMember] = []

    @property
    def member_count(self) -> int:
        """Return the number of members in the team."""
        return len(self.members)

    @property
    def owner_email(self) -> str | None:
        """Return the email of the team owner, if any."""
        for member in self.members:
            if member.is_owner:
                return member.user.email
        return None


class AdminTeamUpdate(msgspec.Struct, gc=False, omit_defaults=True):
    """Update payload for admin team management."""

    name: str | msgspec.UnsetType | None = msgspec.UNSET
    description: str | msgspec.UnsetType | None = msgspec.UNSET
    is_active: bool | msgspec.UnsetType = msgspec.UNSET
