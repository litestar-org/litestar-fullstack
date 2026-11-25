"""User-related account schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

import msgspec

from app.db.models import TeamRoles
from app.lib.schema import CamelizedBaseStruct, Email, Name, Phone, Username


class UserTeam(CamelizedBaseStruct):
    """Team membership summary nested on user responses."""

    team_id: UUID
    team_name: str
    is_owner: bool = False
    role: TeamRoles | None = None

    def __post_init__(self) -> None:
        """Default missing team role to ``TeamRoles.MEMBER``."""
        if self.role is None:
            self.role = TeamRoles.MEMBER


class UserRole(CamelizedBaseStruct):
    """Assigned global role summary nested on user responses."""

    role_id: UUID
    role_slug: str
    role_name: str
    assigned_at: datetime


class OauthAccount(CamelizedBaseStruct):
    """Secret-free summary of a linked external OAuth account."""

    id: UUID
    oauth_name: str
    account_id: str
    account_email: str


class User(CamelizedBaseStruct):
    """Serialized user account response payload."""

    id: UUID
    email: str
    name: str | None = None
    username: str | None = None
    phone: str | None = None
    is_superuser: bool = False
    is_active: bool = False
    is_verified: bool = False
    is_two_factor_enabled: bool = False
    totp_method_id: str | None = None
    has_password: bool = False
    teams: list[UserTeam] = []
    roles: list[UserRole] = []
    oauth_accounts: list[OauthAccount] = []
    avatar_url: str | None = None


class UserCreate(CamelizedBaseStruct):
    """Admin request payload for creating a user account."""

    email: Email
    password: str
    name: Name | None = None
    username: Username | None = None
    phone: Phone | None = None
    is_superuser: bool = False
    is_active: bool = True
    is_verified: bool = False

    def __post_init__(self) -> None:
        """Reject a username that repeats the local part of the email address.

        Raises:
            ValueError: If ``username`` equals the part of ``email`` before the ``@``, ignoring letter case.
        """
        if self.username is not None and self.username == self.email.partition("@")[0].casefold():
            msg = "Username cannot be the same as email local part"
            raise ValueError(msg)


class UserUpdate(CamelizedBaseStruct, omit_defaults=True):
    """Admin request payload for partially updating a user account."""

    email: Email | msgspec.UnsetType | None = msgspec.UNSET
    password: str | msgspec.UnsetType | None = msgspec.UNSET
    name: Name | msgspec.UnsetType | None = msgspec.UNSET
    username: Username | msgspec.UnsetType | None = msgspec.UNSET
    phone: Phone | msgspec.UnsetType | None = msgspec.UNSET
    is_superuser: bool | msgspec.UnsetType | None = msgspec.UNSET
    is_active: bool | msgspec.UnsetType | None = msgspec.UNSET
    is_verified: bool | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self) -> None:
        """Require at least one field.

        Raises:
            ValueError: If no fields are provided.
        """
        fields = (
            self.email,
            self.password,
            self.name,
            self.username,
            self.phone,
            self.is_superuser,
            self.is_active,
            self.is_verified,
        )
        if all(field is msgspec.UNSET for field in fields):
            msg = "At least one field must be provided for update"
            raise ValueError(msg)


class ProfileUpdate(CamelizedBaseStruct, omit_defaults=True):
    """Self-service profile update payload."""

    name: Name | msgspec.UnsetType | None = msgspec.UNSET
    username: Username | msgspec.UnsetType | None = msgspec.UNSET
    phone: Phone | msgspec.UnsetType | None = msgspec.UNSET


class PasswordConfirmation(CamelizedBaseStruct):
    """Optional current password re-confirming a sign-in that is no longer recent."""

    current_password: str | None = None


class PasswordUpdate(CamelizedBaseStruct):
    """Self-service password change request payload."""

    current_password: str
    new_password: str
