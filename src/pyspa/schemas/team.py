# Standard Library
import uuid
from typing import Any, Optional, cast

from pydantic import UUID4, EmailStr, Field

from pyspa import models
from pyspa.schemas.base import CamelizedBaseSchema

# #################################
#
# Workspace Member
#
# #################################


# Properties to receive via API on creation
class WorkspaceMemberCreate(CamelizedBaseSchema):
    user_id: UUID4
    role: models.WorkspaceRoleTypes = models.WorkspaceRoleTypes.MEMBER


# Properties to receive via API on update
class WorkspaceMemberUpdate(CamelizedBaseSchema):
    role: Optional[models.WorkspaceRoleTypes] = models.WorkspaceRoleTypes.MEMBER
    is_owner: Optional[bool] = False


# Additional properties to return via API
class WorkspaceMember(CamelizedBaseSchema):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    email: EmailStr
    full_name: Optional[str]
    role: Optional[models.WorkspaceRoleTypes] = models.WorkspaceRoleTypes.MEMBER
    is_owner: Optional[bool] = False

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: Any) -> "WorkspaceMember":
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
class WorkspaceInvitationCreate(CamelizedBaseSchema):
    workspace_id: UUID4
    role: models.WorkspaceRoleTypes = models.WorkspaceRoleTypes.MEMBER
    email: EmailStr
    user_id: UUID4


# Properties to receive via API on update
class WorkspaceInvitationUpdate(CamelizedBaseSchema):
    workspace_id: UUID4
    role: models.WorkspaceRoleTypes = models.WorkspaceRoleTypes.MEMBER
    email: EmailStr
    is_accepted: bool


# Additional properties to return via API
class WorkspaceInvitation(CamelizedBaseSchema):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    workspace_id: UUID4
    email: EmailStr
    role: models.WorkspaceRoleTypes
    user_id: UUID4
    is_accepted: bool
