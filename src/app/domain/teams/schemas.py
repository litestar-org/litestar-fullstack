from __future__ import annotations

from uuid import UUID  # noqa: TCH003

from pydantic import EmailStr  # noqa: TCH002

from app.domain.teams.models import TeamRoles
from app.lib.schema import CamelizedBaseModel

__all__ = [
    "Team",
    "TeamCreate",
    "TeamMember",
    "TeamMemberCreate",
    "TeamMemberUpdate",
    "TeamUpdate",
]


# Properties to receive via API on creation
class TeamCreate(CamelizedBaseModel):
    """Team properties received on create."""

    name: str
    description: str | None


# Properties to receive via API on update
class TeamUpdate(CamelizedBaseModel):
    """Team properties received on update."""

    name: str | None = None
    description: str | None


# Additional properties to return via API
class Team(CamelizedBaseModel):
    """Team Response properties."""

    id: UUID
    slug: str
    name: str
    description: str | None
    members: list[TeamMember] = []


# #################################
#
# Team Member
#
# #################################


# Properties to receive via API on creation
class TeamMemberCreate(CamelizedBaseModel):
    """Team Member Create."""

    user_id: UUID
    role: TeamRoles = TeamRoles.MEMBER


# Properties to receive via API on update
class TeamMemberUpdate(CamelizedBaseModel):
    """Team Member Update."""

    user_id: UUID
    role: TeamRoles | None = TeamRoles.MEMBER
    is_owner: bool | None = False


# Additional properties to return via API
class TeamMember(CamelizedBaseModel):
    """Team member information."""

    id: UUID
    user_id: UUID
    user_email: EmailStr
    user_name: str | None
    role: TeamRoles = TeamRoles.MEMBER
    is_owner: bool = False


Team.update_forward_refs()
