"""Teams domain schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

from app.db.models.team_roles import TeamRoles
from app.schemas.base import CamelizedBaseStruct, Message

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

__all__ = (
    "Message",
    "Team",
    "TeamCreate",
    "TeamInvitation",
    "TeamInvitationCreate",
    "TeamMember",
    "TeamMemberModify",
    "TeamMemberUpdate",
    "TeamTag",
    "TeamUpdate",
)


class TeamTag(CamelizedBaseStruct):
    id: UUID
    slug: str
    name: str


class TeamMember(CamelizedBaseStruct):
    id: UUID
    user_id: UUID
    email: str
    name: str | None = None
    role: TeamRoles | None = None
    is_owner: bool | None = False

    def __post_init__(self) -> None:
        """Set default role if not provided."""
        if self.role is None:
            self.role = TeamRoles.MEMBER


class Team(CamelizedBaseStruct):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    is_active: bool = True
    members: list[TeamMember] = []
    tags: list[TeamTag] = []


class TeamCreate(CamelizedBaseStruct):
    name: str
    description: str | None = None
    tags: list[str] = []


class TeamUpdate(CamelizedBaseStruct, omit_defaults=True):
    name: str | msgspec.UnsetType | None = msgspec.UNSET
    description: str | msgspec.UnsetType | None = msgspec.UNSET
    tags: list[str] | msgspec.UnsetType | None = msgspec.UNSET


class TeamMemberModify(CamelizedBaseStruct):
    """Team Member Modify."""

    user_name: str


class TeamMemberUpdate(CamelizedBaseStruct):
    """Team Member Update."""

    role: TeamRoles


class TeamInvitationCreate(CamelizedBaseStruct):
    email: str
    role: TeamRoles


class TeamInvitation(CamelizedBaseStruct):
    id: UUID
    email: str
    role: TeamRoles
    created_at: datetime
    updated_at: datetime
    is_accepted: bool = False
