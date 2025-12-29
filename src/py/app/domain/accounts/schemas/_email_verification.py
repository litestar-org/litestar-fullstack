"""Email verification schemas."""

from app.lib.validation import validate_email
from app.lib.schema import CamelizedBaseStruct


class EmailVerificationRequest(CamelizedBaseStruct):
    """Request schema for requesting email verification."""

    email: str

    def __post_init__(self) -> None:
        """Validate email."""
        self.email = validate_email(self.email)


class EmailVerificationConfirm(CamelizedBaseStruct):
    """Confirmation schema for email verification."""

    token: str


class EmailVerificationSent(CamelizedBaseStruct):
    """Response for email verification request."""

    message: str
    token: str | None = None


class EmailVerificationStatus(CamelizedBaseStruct):
    """Verification status response."""

    is_verified: bool
