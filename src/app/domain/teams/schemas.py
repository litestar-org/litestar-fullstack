from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
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


if TYPE_CHECKING:
    from app.domain.accounts.models import User


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
    members: list[TeamMember] | None = []
    member_count: int = 0

    @classmethod
    def from_orm(cls, obj: Any) -> Team:
        """From ORM.

        Append the member count.
        """
        # `obj` is the orm model instance
        if obj.members:
            obj.member_count = len(obj.members)
        return super().from_orm(obj)


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
    email: EmailStr | None
    name: str | None
    role: TeamRoles | None = TeamRoles.MEMBER
    is_owner: bool | None = False

    @classmethod
    def from_orm(cls, obj: Any) -> TeamMember:
        """From ORM.

        flattens user and email to the outgoing TeamMember object.
        """
        # `obj` is the orm model instance

        if obj.user:
            user = cast("User", obj.user)
            obj.name = user.name
            obj.email = user.email
        return super().from_orm(obj)


Team.update_forward_refs()
