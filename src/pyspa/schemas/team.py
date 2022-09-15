# Standard Library
import uuid
from typing import Any, Optional, cast

from pydantic import UUID4, EmailStr, Field

from pyspa import models
from pyspa.schemas.base import CamelizedBaseSchema
from pyspa.schemas.upload import Upload

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


# Properties to receive via API on update
class TeamUpdate(CamelizedBaseSchema):
    """Team properties received on update"""

    name: Optional[str] = None
    description: Optional[str]
    organization_id: Optional[UUID4]


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
    role: models.TeamRoleTypes = models.TeamRoleTypes.MEMBER


# Properties to receive via API on update
class TeamMemberUpdate(CamelizedBaseSchema):
    role: Optional[models.TeamRoleTypes] = models.TeamRoleTypes.MEMBER
    is_owner: Optional[bool] = False


# Additional properties to return via API
class TeamMember(CamelizedBaseSchema):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    email: EmailStr
    full_name: Optional[str]
    role: Optional[models.TeamRoleTypes] = models.TeamRoleTypes.MEMBER
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


# #################################
#
# Invitation
#
# #################################
# Shared properties


# Properties to receive via API on creation
class TeamInvitationCreate(CamelizedBaseSchema):
    team_id: UUID4
    role: models.TeamRoleTypes = models.TeamRoleTypes.MEMBER
    email: EmailStr
    user_id: UUID4


# Properties to receive via API on update
class TeamInvitationUpdate(CamelizedBaseSchema):
    team_id: UUID4
    role: models.TeamRoleTypes = models.TeamRoleTypes.MEMBER
    email: EmailStr
    is_accepted: bool


# Additional properties to return via API
class TeamInvitation(CamelizedBaseSchema):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    team_id: UUID4
    email: EmailStr
    role: models.TeamRoleTypes
    user_id: UUID4
    is_accepted: bool


Team.update_forward_refs()
