from __future__ import annotations

import hashlib
from datetime import datetime  # noqa: TCH003
from functools import cached_property
from uuid import UUID  # noqa: TCH003

import msgspec

from app.db.models.team_roles import TeamRoles
from app.lib.schema import CamelizedBaseStruct

__all__ = (
    "AccountLogin",
    "AccountRegister",
    "UserRoleAdd",
    "UserRoleRevoke",
    "UserCreate",
    "User",
    "UserRole",
    "UserTeam",
    "UserUpdate",
)


class UserTeam(CamelizedBaseStruct):
    """Holds team details for a user.

    This is nested in the User Model for 'team'
    """

    team_id: UUID
    team_name: str
    is_owner: bool = False
    role: TeamRoles = TeamRoles.MEMBER


class UserRole(CamelizedBaseStruct):
    """Holds role details for a user.

    This is nested in the User Model for 'roles'
    """

    role_id: UUID
    role_slug: str
    role_name: str
    assigned_at: datetime


class OauthAccount(CamelizedBaseStruct):
    """Holds linked Oauth details for a user."""

    id: UUID
    oauth_name: str
    access_token: str
    account_id: str
    account_email: str
    expires_at: int | None = None
    refresh_token: str | None = None


class User(CamelizedBaseStruct):
    """User properties to use for a response."""

    id: UUID
    email: str
    name: str | None = None
    is_superuser: bool = False
    is_active: bool = False
    is_verified: bool = False
    teams: list[UserTeam] = []
    roles: list[UserRole] = []
    oauth_accounts: list[OauthAccount] = []
    avatar_url: str | None = None

    def __post_init__(self) -> None:
        if not self.avatar_url:
            self.avatar_url = f"https://www.gravatar.com/avatar/{self.gravatar_id}?s=128&d=identicon"

    @cached_property
    def gravatar_id(self) -> str:
        """Generate the has required for a Gravatar Avatar lookup"""
        # https://en.gravatar.com/site/implement/hash/
        email = self.email.lower().strip().encode("utf-8")
        return hashlib.md5(email).hexdigest()  # noqa: S324


class UserCreate(CamelizedBaseStruct):
    email: str
    password: str
    name: str | None = None
    is_superuser: bool = False
    is_active: bool = True
    is_verified: bool = False


class UserUpdate(CamelizedBaseStruct, omit_defaults=True):
    email: str | None | msgspec.UnsetType = msgspec.UNSET
    password: str | None | msgspec.UnsetType = msgspec.UNSET
    name: str | None | msgspec.UnsetType = msgspec.UNSET
    is_superuser: bool | None | msgspec.UnsetType = msgspec.UNSET
    is_active: bool | None | msgspec.UnsetType = msgspec.UNSET
    is_verified: bool | None | msgspec.UnsetType = msgspec.UNSET


class AccountLogin(CamelizedBaseStruct):
    username: str
    password: str


class AccountRegister(CamelizedBaseStruct):
    email: str
    password: str
    name: str | None = None


class UserRoleAdd(CamelizedBaseStruct):
    """User role add ."""

    user_name: str


class UserRoleRevoke(CamelizedBaseStruct):
    """User role revoke ."""

    user_name: str
