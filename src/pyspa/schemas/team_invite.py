# Standard Library
import uuid

from pydantic import UUID4, EmailStr, Field

from pyspa import models
from pyspa.schemas.base import CamelizedBaseSchema


# Properties to receive via API on creation
class TeamInvitationCreate(CamelizedBaseSchema):
    team_id: UUID4
    role: models.TeamRoles = models.TeamRoles.MEMBER
    email: EmailStr
    user_id: UUID4


# Properties to receive via API on update
class TeamInvitationUpdate(CamelizedBaseSchema):
    team_id: UUID4
    role: models.TeamRoles = models.TeamRoles.MEMBER
    email: EmailStr
    is_accepted: bool


# Additional properties to return via API
class TeamInvitation(CamelizedBaseSchema):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    team_id: UUID4
    email: EmailStr
    role: models.TeamRoles
    invited_by: UUID4
    is_accepted: bool
