from __future__ import annotations

from datetime import datetime  # noqa: TCH003

from pydantic import UUID4, EmailStr  # noqa: TCH002
from pydantic.types import SecretStr  # noqa: TCH002

from app.domain.teams.models import TeamRoles
from app.lib.schema import CamelizedBaseModel

__all__ = [
    "User",
    "UserCreate",
    "UserLogin",
    "UserPasswordConfirm",
    "UserPasswordUpdate",
    "UserRegister",
    "UserTeam",
    "UserUpdate",
]


class User(CamelizedBaseModel):
    """User properties to use for a response."""

    id: UUID4
    email: EmailStr
    name: str | None
    is_superuser: bool
    is_active: bool
    is_verified: bool
    created: datetime
    updated: datetime
    teams: list[UserTeam] = []


class UserTeam(CamelizedBaseModel):
    """Holds teams details for a user.

    This is nested in the User Model for 'team'
    """

    team_id: UUID4
    team_name: str
    is_owner: bool = False
    role: TeamRoles = TeamRoles.MEMBER


class UserRegister(CamelizedBaseModel):
    """User Registration Input."""

    email: EmailStr
    password: SecretStr
    name: str | None = None


class UserLogin(CamelizedBaseModel):
    """Properties required to log in."""

    username: str
    password: SecretStr


class UserPasswordUpdate(CamelizedBaseModel):
    """Properties to receive for user updates."""

    current_password: SecretStr
    new_password: SecretStr


class UserPasswordConfirm(CamelizedBaseModel):
    """Confirm Password DTO."""

    password: SecretStr


# Properties to receive via API on creation
class UserCreate(CamelizedBaseModel):
    """User Create DTO."""

    email: EmailStr
    password: SecretStr
    name: str | None = None
    is_superuser: bool | None = False
    is_active: bool | None = True
    is_verified: bool | None = False


class UserUpdate(CamelizedBaseModel):
    """User update DTO."""

    email: EmailStr | None = None
    name: str | None = None
    is_superuser: bool | None = False
    is_active: bool | None = False
    is_verified: bool | None = False


User.update_forward_refs()
