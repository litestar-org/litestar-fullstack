"""User-related account schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

import msgspec

from app.db.models._team_roles import TeamRoles
from app.lib.schema import CamelizedBaseStruct
from app.lib.validation import validate_email, validate_name, validate_password, validate_phone, validate_username


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

    email: str
    password: str
    name: str | None = None
    username: str | None = None
    phone: str | None = None
    is_superuser: bool = False
    is_active: bool = True
    is_verified: bool = False

    def __post_init__(self) -> None:
        """Validate user creation fields.

        Raises:
            ValueError: If any field fails validation or ``username`` matches the email local part.
        """
        self.email = validate_email(self.email)
        self.password = validate_password(self.password)
        if self.name is not None:
            self.name = validate_name(self.name)
        if self.username is not None:
            self.username = validate_username(self.username)
        if self.phone is not None:
            self.phone = validate_phone(self.phone)
        if self.username and self.email and self.username == self.email.split("@")[0]:
            msg = "Username cannot be the same as email local part"
            raise ValueError(msg)


class UserUpdate(CamelizedBaseStruct, omit_defaults=True):
    """Admin request payload for partially updating a user account."""

    email: str | msgspec.UnsetType | None = msgspec.UNSET
    password: str | msgspec.UnsetType | None = msgspec.UNSET
    name: str | msgspec.UnsetType | None = msgspec.UNSET
    username: str | msgspec.UnsetType | None = msgspec.UNSET
    phone: str | msgspec.UnsetType | None = msgspec.UNSET
    is_superuser: bool | msgspec.UnsetType | None = msgspec.UNSET
    is_active: bool | msgspec.UnsetType | None = msgspec.UNSET
    is_verified: bool | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self) -> None:
        """Validate populated update fields and require at least one field.

        Raises:
            ValueError: If no fields are provided or any populated field fails validation.
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
        if isinstance(self.email, str):
            self.email = validate_email(self.email)
        if isinstance(self.password, str):
            self.password = validate_password(self.password)
        if isinstance(self.name, str):
            self.name = validate_name(self.name)
        if isinstance(self.username, str):
            self.username = validate_username(self.username)
        if isinstance(self.phone, str):
            self.phone = validate_phone(self.phone)


class ProfileUpdate(CamelizedBaseStruct, omit_defaults=True):
    """Self-service profile update payload."""

    name: str | msgspec.UnsetType | None = msgspec.UNSET
    username: str | msgspec.UnsetType | None = msgspec.UNSET
    phone: str | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self) -> None:
        """Validate provided profile fields."""
        if isinstance(self.name, str):
            self.name = validate_name(self.name)
        if isinstance(self.username, str):
            self.username = validate_username(self.username)
        if isinstance(self.phone, str):
            self.phone = validate_phone(self.phone)


class PasswordUpdate(CamelizedBaseStruct):
    """Self-service password change request payload."""

    current_password: str
    new_password: str

    def __post_init__(self) -> None:
        """Validate new password strength."""
        self.new_password = validate_password(self.new_password)
