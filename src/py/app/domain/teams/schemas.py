"""Teams domain schemas."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import msgspec

from app.schemas.base import CamelizedBaseStruct, Message

if TYPE_CHECKING:
    from app.db import models as m

__all__ = (
    "Message",
    "Team",
    "TeamCreate",
    "TeamInvitation",
    "TeamInvitationCreate",
    "TeamMember",
    "TeamMemberModify",
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
    role: m.TeamRoles | None = None  # type: ignore[name-defined]
    is_owner: bool | None = False

    def __post_init__(self) -> None:
        """Set default role if not provided."""
        if self.role is None:
            from app.db import models as m

            self.role = m.TeamRoles.MEMBER


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


class TeamInvitationCreate(CamelizedBaseStruct):
    email: str
    role: m.TeamRoles  # type: ignore[name-defined]


class TeamInvitation(CamelizedBaseStruct):
    id: UUID
    email: str
    role: m.TeamRoles  # type: ignore[name-defined]
    created_at: datetime
    updated_at: datetime
