"""Multi-factor authentication schemas."""

from datetime import datetime

import msgspec


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
