"""User-related account schemas."""

from datetime import datetime
from uuid import UUID

import msgspec

from app.db.models._team_roles import TeamRoles
from app.lib.schema import CamelizedBaseStruct
from app.lib.validation import validate_email, validate_name, validate_password, validate_phone, validate_username


class UserTeam(CamelizedBaseStruct):
    """Holds team details for a user.

    This is nested in the User Model for 'team'
    """

    team_id: UUID
    team_name: str
    is_owner: bool = False
    role: TeamRoles | None = None

    def __post_init__(self) -> None:
        """Set default role if not provided."""
        if self.role is None:
            from app.db.models._team_roles import TeamRoles

            self.role = TeamRoles.MEMBER


class UserRole(CamelizedBaseStruct):
    """Holds role details for a user.

    This is nested in the User Model for 'roles'
    """

    role_id: UUID
    role_slug: str
    role_name: str
    assigned_at: datetime


class OauthAccount(CamelizedBaseStruct):
    """Holds linked OAuth details for a user.

    Note: Sensitive fields (access_token, refresh_token, expires_at) are
    intentionally excluded from this schema to prevent token leakage to
    the frontend. These fields should only be accessed server-side.
    """

    id: UUID
    oauth_name: str
    account_id: str
    account_email: str


class User(CamelizedBaseStruct):
    """User properties to use for a response."""

    id: UUID
    email: str
    name: str | None = None
    username: str | None = None
    phone: str | None = None
    is_superuser: bool = False
    is_active: bool = False
    is_verified: bool = False
    is_two_factor_enabled: bool = False
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

        self.email = validate_email(self.email)
        self.password = validate_password(self.password)
        if self.name is not None:
            self.name = validate_name(self.name)
        if self.username is not None:
            self.username = validate_username(self.username)
        if self.phone is not None:
            self.phone = validate_phone(self.phone)

        if self.username and self.email:
            email_local = self.email.split("@")[0]
            if self.username == email_local:
                msg = "Username cannot be the same as email local part"
                raise ValueError(msg)


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
    name: str | msgspec.UnsetType | None = msgspec.UNSET
    username: str | msgspec.UnsetType | None = msgspec.UNSET
    phone: str | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self) -> None:
        """Validate fields if provided."""
        if isinstance(self.name, str):
            self.name = validate_name(self.name)
        if isinstance(self.username, str):
            self.username = validate_username(self.username)
        if isinstance(self.phone, str):
            self.phone = validate_phone(self.phone)
