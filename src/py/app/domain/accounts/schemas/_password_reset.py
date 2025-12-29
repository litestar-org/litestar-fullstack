"""Password reset schemas."""

from uuid import UUID

import msgspec

from app.lib.validation import validate_email, validate_password


class ForgotPasswordRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to initiate password reset flow."""

    email: str

    def __post_init__(self) -> None:
        """Validate email."""
        self.email = validate_email(self.email)


class PasswordResetSent(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Confirmation that password reset email was sent."""

    message: str
    expires_in_minutes: int = 60


class ValidateResetTokenRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to validate a reset token."""

    token: str


class ResetTokenValidation(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Result of reset token validation."""

    valid: bool
    user_id: UUID | None = None
    expires_at: str | None = None


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
