# Standard Library
from typing import Any, Optional

from pydantic import UUID4, EmailStr, root_validator
from pydantic.types import SecretStr

from pyspa import models
from pyspa.schemas.base import CamelizedBaseSchema


class User(CamelizedBaseSchema):
    """User properties to use for a response"""

    id: UUID4
    email: EmailStr
    full_name: Optional[str]
    is_superuser: bool
    is_active: bool
    is_verified: bool
    team_count: Optional[int] = 0
    teams: Optional[list["UserTeam"]] = []

    @classmethod
    def from_orm(cls, obj: Any) -> "User":
        """Appends additional data from nested tables to the user object"""
        if getattr(obj, "teams", None):
            obj.team_count = len(obj.teams)
        return super().from_orm(obj)


class UserTeam(CamelizedBaseSchema):
    """Holds teams details for a user

    This is nested in the User Model for 'team'
    """

    team_id: "Optional[UUID4]" = None
    name: "Optional[str]" = None
    is_owner: "Optional[bool]" = False
    role: "Optional[models.TeamRoleTypes]" = models.TeamRoleTypes.MEMBER

    @classmethod
    def from_orm(cls, obj: Any) -> "UserTeam":
        """Flatten team details to the user membership object"""
        if getattr(obj, "team", None) and getattr(obj.team, "name", None):
            obj.name = obj.team.name
        return super().from_orm(obj)


class UserSignup(CamelizedBaseSchema):
    email: EmailStr
    password: SecretStr
    full_name: Optional[str] = None
    team_name: Optional[str] = None
    invitation_id: Optional[int] = None

    @root_validator(pre=True)
    def team_or_invitation_but_not_both(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("team_name", None) and values.get("invitation_id", None):
            raise ValueError(
                "Unable to accept invitation and create a default team",
            )
        return values


class UserLogin(CamelizedBaseSchema):
    """Properties required to log in"""

    username: str
    password: SecretStr


class UserPasswordUpdate(CamelizedBaseSchema):
    """Properties to receive for user updates"""

    current_password: SecretStr
    new_password: SecretStr


class UserPasswordConfirm(CamelizedBaseSchema):
    """Properties to receive for user updates"""

    password: SecretStr


# Properties to receive via API on creation
class UserCreate(CamelizedBaseSchema):
    """User Create Properties"""

    email: EmailStr
    password: SecretStr
    full_name: Optional[str] = None
    team_name: Optional[str] = None
    invitation_id: Optional[int] = None
    is_superuser: Optional[bool] = False
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False

    @root_validator(pre=True)
    def team_or_invitation_but_not_both(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("team_name", None) and values.get("invitation_id", None):
            raise ValueError(
                "Unable to accept invitation and create a default team",
            )
        return values


# Properties to receive via API on update
class UserUpdate(CamelizedBaseSchema):
    """Properties to receive for user updates"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_superuser: Optional[bool] = False
    is_active: Optional[bool] = False
    is_verified: Optional[bool] = False


User.update_forward_refs()
