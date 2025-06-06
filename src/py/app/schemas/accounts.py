from datetime import datetime
from uuid import UUID

import msgspec

from app.db.models.team_roles import TeamRoles
from app.lib.validation import validate_email, validate_name, validate_password, validate_phone, validate_username
from app.schemas.base import CamelizedBaseStruct

__all__ = (
    "AccountLogin",
    "AccountRegister",
    "EmailVerificationConfirm",
    "EmailVerificationRequest",
    "User",
    "UserCreate",
    "UserRole",
    "UserRoleAdd",
    "UserRoleRevoke",
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
    email: str  # Already validated in DB, so plain str for response
    name: str | None = None
    username: str | None = None
    phone: str | None = None
    is_superuser: bool = False
    is_active: bool = False
    is_verified: bool = False
    has_password: bool = False
    teams: list[UserTeam] = []
    roles: list[UserRole] = []
    oauth_accounts: list[OauthAccount] = []
    avatar_url: str | None = None


class UserCreate(CamelizedBaseStruct):
    email: str
    password: str
    name: str | None = None
    username: str | None = None
    phone: str | None = None
    is_superuser: bool = False
    is_active: bool = True
    is_verified: bool = False

    def __post_init__(self) -> None:
        """Additional validation after field validation."""
        # Validate fields
        self.email = validate_email(self.email)
        self.password = validate_password(self.password)
        if self.name is not None:
            self.name = validate_name(self.name)
        if self.username is not None:
            self.username = validate_username(self.username)
        if self.phone is not None:
            self.phone = validate_phone(self.phone)

        # Custom cross-field validation
        if self.username and self.email:
            email_local = self.email.split("@")[0]
            if self.username == email_local:
                raise ValueError("Username cannot be the same as email local part")


class UserUpdate(CamelizedBaseStruct, omit_defaults=True):
    email: str | msgspec.UnsetType | None = msgspec.UNSET
    password: str | msgspec.UnsetType | None = msgspec.UNSET
    name: str | msgspec.UnsetType | None = msgspec.UNSET
    username: str | msgspec.UnsetType | None = msgspec.UNSET
    phone: str | msgspec.UnsetType | None = msgspec.UNSET
    is_superuser: bool | msgspec.UnsetType | None = msgspec.UNSET
    is_active: bool | msgspec.UnsetType | None = msgspec.UNSET
    is_verified: bool | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self) -> None:
        """Ensure at least one field is provided for update and validate fields."""
        fields = [
            self.email,
            self.password,
            self.name,
            self.username,
            self.phone,
            self.is_superuser,
            self.is_active,
            self.is_verified,
        ]
        if all(field is msgspec.UNSET for field in fields):
            raise ValueError("At least one field must be provided for update")

        # Validate fields if provided
        if self.email not in (msgspec.UNSET, None):
            self.email = validate_email(self.email)
        if self.password not in (msgspec.UNSET, None):
            self.password = validate_password(self.password)
        if self.name not in (msgspec.UNSET, None):
            self.name = validate_name(self.name)
        if self.username not in (msgspec.UNSET, None):
            self.username = validate_username(self.username)
        if self.phone not in (msgspec.UNSET, None):
            self.phone = validate_phone(self.phone)


class AccountLogin(CamelizedBaseStruct):
    username: str  # Use email for login
    password: str  # Don't validate password strength on login

    def __post_init__(self) -> None:
        """Validate email format for username."""
        self.username = validate_email(self.username)


class PasswordUpdate(CamelizedBaseStruct):
    current_password: str  # Don't validate strength on current
    new_password: str  # Validate new password strength

    def __post_init__(self) -> None:
        """Validate new password strength."""
        self.new_password = validate_password(self.new_password)


class PasswordVerify(CamelizedBaseStruct):
    current_password: str


class ProfileUpdate(CamelizedBaseStruct, omit_defaults=True):
    name: str | msgspec.UnsetType | None = msgspec.UNSET
    username: str | msgspec.UnsetType | None = msgspec.UNSET
    phone: str | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self) -> None:
        """Validate fields if provided."""
        if self.name not in (msgspec.UNSET, None) and isinstance(self.name, str):
            self.name = validate_name(self.name)
        if self.username not in (msgspec.UNSET, None) and isinstance(self.username, str):
            self.username = validate_username(self.username)
        if self.phone not in (msgspec.UNSET, None) and isinstance(self.phone, str):
            self.phone = validate_phone(self.phone)


class AccountRegister(CamelizedBaseStruct):
    email: str
    password: str
    name: str | None = None
    username: str | None = None
    initial_team_name: str | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self) -> None:
        """Validate fields."""
        self.email = validate_email(self.email)
        self.password = validate_password(self.password)
        if self.name is not None:
            self.name = validate_name(self.name)
        if self.username is not None:
            self.username = validate_username(self.username)


class UserRoleAdd(CamelizedBaseStruct):
    """User role add ."""

    user_name: str


class UserRoleRevoke(CamelizedBaseStruct):
    """User role revoke ."""

    user_name: str


class EmailVerificationRequest(CamelizedBaseStruct):
    """Request schema for requesting email verification."""

    email: str

    def __post_init__(self) -> None:
        """Validate email."""
        self.email = validate_email(self.email)


class EmailVerificationConfirm(CamelizedBaseStruct):
    """Confirmation schema for email verification."""

    token: str
