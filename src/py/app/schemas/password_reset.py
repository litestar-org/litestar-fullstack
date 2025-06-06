"""Password reset schemas for API validation."""

from __future__ import annotations

from uuid import UUID

import msgspec

from app.lib.validation import validate_email, validate_password


class ForgotPasswordRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to initiate password reset flow."""

    email: str

    def __post_init__(self) -> None:
        """Validate email."""
        self.email = validate_email(self.email)


class ForgotPasswordResponse(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Response after requesting password reset."""

    message: str
    expires_in_minutes: int = 60  # 1 hour default


class ValidateResetTokenRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to validate a reset token."""

    token: str


class ValidateResetTokenResponse(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Response for token validation."""

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
            raise ValueError("Passwords do not match")
        self.password = validate_password(self.password)


class ResetPasswordResponse(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Response after successful password reset."""

    message: str
    user_id: UUID
