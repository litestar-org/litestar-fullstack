# Standard Library
import uuid
from typing import Any, Optional, cast

from pydantic import UUID4, EmailStr, Field

from pyspa import models
from pyspa.schemas.base import CamelizedBaseSchema
from pyspa.schemas.team_invite import TeamInvitation  # noqa: TC002
from pyspa.schemas.upload import Upload  # noqa: TC002

# #################################
#
# Team
#
# #################################
# Shared properties


# Properties to receive via API on creation
class TeamCreate(CamelizedBaseSchema):
    """Team properties received on create"""

    name: str
    description: Optional[str]
    owner_id: UUID4


# Properties to receive via API on update
class TeamUpdate(CamelizedBaseSchema):
    """Team properties received on update"""

    name: Optional[str] = None
    description: Optional[str]


# Additional properties to return via API
class Team(CamelizedBaseSchema):
    """Team Response properties"""

    id: UUID4 = Field(default_factory=uuid.uuid4)
    name: Optional[str]
    description: Optional[str]
    members: Optional[list["TeamMember"]] = []
    uploads: Optional[list["Upload"]] = []
    pending_invitations: Optional[list["TeamInvitation"]] = []


# #################################
#
# Team Member
#
# #################################


# Properties to receive via API on creation
class TeamMemberCreate(CamelizedBaseSchema):
    user_id: UUID4
    role: models.TeamRoles = models.TeamRoles.MEMBER


# Properties to receive via API on update
class TeamMemberUpdate(CamelizedBaseSchema):
    role: Optional[models.TeamRoles] = models.TeamRoles.MEMBER
    is_owner: Optional[bool] = False


# Additional properties to return via API
class TeamMember(CamelizedBaseSchema):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    email: EmailStr
    full_name: Optional[str]
    role: Optional[models.TeamRoles] = models.TeamRoles.MEMBER
    is_owner: Optional[bool] = False

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: Any) -> "TeamMember":
        """
        Format organization details for the User object

        The relation for a user to an organ is 1 to many (org can have many users,
         user can belong to a single org)
        """
        # `obj` is the orm model instance
        if getattr(obj, "member"):
            member = cast("models.User", obj.member)
            obj.full_name = member.full_name
            obj.email = member.email
            obj.id = member.id
        return super().from_orm(obj)


Team.update_forward_refs()
