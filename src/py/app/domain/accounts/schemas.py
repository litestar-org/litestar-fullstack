"""Account domain schemas for users, auth, OAuth, roles, and password reset."""

from datetime import datetime
from typing import Literal
from uuid import UUID

import msgspec

from app.db.models.team_roles import TeamRoles
from app.lib.validation import validate_email, validate_name, validate_password, validate_phone, validate_username
from app.schemas.base import CamelizedBaseStruct, Message

__all__ = (  # noqa: RUF022 - Intentionally organized by category
    # Common
    "Message",
    # User/Account schemas
    "AccountLogin",
    "AccountRegister",
    "EmailVerificationConfirm",
    "EmailVerificationRequest",
    "OauthAccount",
    "PasswordUpdate",
    "PasswordVerify",
    "ProfileUpdate",
    "User",
    "UserCreate",
    "UserRole",
    "UserRoleAdd",
    "UserRoleRevoke",
    "UserTeam",
    "UserUpdate",
    # Role schemas
    "Role",
    "RoleCreate",
    "RoleUpdate",
    # OAuth schemas
    "OAuthAccountInfo",
    "OAuthAuthorizationRequest",
    "OAuthAuthorization",
    "OAuthCallbackRequest",
    "OAuthLinkRequest",
    # Password reset schemas
    "ForgotPasswordRequest",
    "PasswordResetSent",
    "ResetPasswordRequest",
    "PasswordResetComplete",
    "ValidateResetTokenRequest",
    "ResetTokenValidation",
    # Session/Refresh token schemas
    "ActiveSession",
    "SessionList",
    "TokenRefresh",
    # MFA schemas
    "MfaSetup",
    "MfaConfirm",
    "MfaBackupCodes",
    "MfaDisable",
    "MfaChallenge",
    "MfaVerifyResult",
    "MfaStatus",
    "LoginMfaChallenge",
)


# =============================================================================
# User/Account Schemas
# =============================================================================


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
            from app.db.models.team_roles import TeamRoles

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

        # Validate fields if provided
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
        if isinstance(self.name, str):
            self.name = validate_name(self.name)
        if isinstance(self.username, str):
            self.username = validate_username(self.username)
        if isinstance(self.phone, str):
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


# =============================================================================
# Role Schemas
# =============================================================================


class Role(CamelizedBaseStruct):
    """Holds role details for a user.

    This is nested in the User Model for 'roles'
    """

    id: UUID
    slug: str
    name: str
    created_at: datetime
    updated_at: datetime


class RoleCreate(CamelizedBaseStruct):
    name: str


class RoleUpdate(CamelizedBaseStruct):
    name: str | msgspec.UnsetType | None = msgspec.UNSET


# =============================================================================
# OAuth Schemas
# =============================================================================


class OAuthAuthorizationRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth authorization request payload."""

    provider: Literal["google"]
    redirect_url: str | None = None


class OAuthAuthorization(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth authorization URL and state."""

    authorization_url: str
    state: str | None = None


class OAuthCallbackRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth callback request."""

    code: str
    provider: Literal["google"]
    state: str | None = None


class OAuthLinkRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to link/unlink OAuth account."""

    provider: Literal["google"]


class OAuthAccountInfo(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth account information."""

    provider: str
    oauth_id: str
    email: str
    linked_at: datetime
    name: str | None = None
    avatar_url: str | None = None
    last_login_at: datetime | None = None


# =============================================================================
# Password Reset Schemas
# =============================================================================


class ForgotPasswordRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to initiate password reset flow."""

    email: str

    def __post_init__(self) -> None:
        """Validate email."""
        self.email = validate_email(self.email)


class PasswordResetSent(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Confirmation that password reset email was sent."""

    message: str
    expires_in_minutes: int = 60  # 1 hour default


class ValidateResetTokenRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to validate a reset token."""

    token: str


class ResetTokenValidation(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Result of reset token validation."""

    valid: bool
    user_id: UUID | None = None
    expires_at: str | None = None  # ISO datetime string


class ResetPasswordRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to reset password with token."""

    token: str
    password: str
    password_confirm: str

    def __post_init__(self) -> None:
        """Validate passwords match and password strength."""
        if self.password != self.password_confirm:
            msg = "Passwords do not match"
            raise ValueError(msg)
        self.password = validate_password(self.password)


class PasswordResetComplete(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Confirmation that password was reset successfully."""

    message: str
    user_id: UUID


# =============================================================================
# Session/Refresh Token Schemas
# =============================================================================


class ActiveSession(msgspec.Struct, gc=False, array_like=True, omit_defaults=True, kw_only=True):
    """Information about an active session (refresh token)."""

    id: UUID
    created_at: datetime
    expires_at: datetime
    device_info: str | None = None
    is_current: bool = False


class SessionList(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """List of active user sessions."""

    sessions: list[ActiveSession]
    count: int


class TokenRefresh(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Confirmation that token was refreshed."""

    message: str = "Token refreshed successfully"


# =============================================================================
# MFA Schemas
# =============================================================================


class MfaSetup(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """MFA setup data with QR code and secret."""

    secret: str
    """The TOTP secret (base32 encoded)."""
    qr_code: str
    """Base64 encoded PNG image of the QR code."""
    provisioning_uri: str
    """The otpauth:// URI for manual entry."""


class MfaConfirm(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """TOTP code to confirm MFA setup."""

    code: str
    """The 6-digit TOTP code from the authenticator app."""


class MfaBackupCodes(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Backup codes for MFA recovery."""

    codes: list[str]
    """List of one-time use backup codes (shown once)."""
    message: str = "Save these backup codes securely. They will not be shown again."


class MfaDisable(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Password confirmation to disable MFA."""

    password: str
    """Current password for verification."""


class MfaChallenge(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """TOTP code or recovery code for MFA verification."""

    code: str | None = None
    """6-digit TOTP code from authenticator app."""
    recovery_code: str | None = None
    """Backup recovery code (8 hex characters)."""

    def __post_init__(self) -> None:
        """Validate that exactly one verification method is provided."""
        if not self.code and not self.recovery_code:
            msg = "Either code or recovery_code must be provided"
            raise ValueError(msg)
        if self.code and self.recovery_code:
            msg = "Provide only one of code or recovery_code, not both"
            raise ValueError(msg)


class MfaVerifyResult(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Result of MFA verification attempt."""

    verified: bool
    """Whether the verification was successful."""
    used_backup_code: bool = False
    """Whether a backup code was used."""
    remaining_backup_codes: int | None = None
    """Number of remaining backup codes (if backup code was used)."""


class MfaStatus(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Current MFA status for a user."""

    enabled: bool
    """Whether MFA is currently enabled."""
    confirmed_at: datetime | None = None
    """When MFA was enabled/confirmed."""
    backup_codes_remaining: int | None = None
    """Number of remaining backup codes."""


class LoginMfaChallenge(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Login result when MFA verification is required."""

    mfa_required: bool = True
    """Always true - indicates MFA verification is needed."""
    message: str = "MFA verification required"
    """Message explaining the login state."""
