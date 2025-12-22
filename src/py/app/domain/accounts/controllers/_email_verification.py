"""Email Verification Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED

from app.domain.accounts.dependencies import provide_email_verification_service, provide_users_service
from app.domain.accounts.schemas import EmailVerificationConfirm, EmailVerificationRequest, User
from app.lib.email import email_service
from app.lib.email.service import UserProtocol

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.accounts.services import EmailVerificationTokenService, UserService


class EmailVerificationController(Controller):
    """Email verification operations."""

    path = "/api/email-verification"
    tags = ["Access"]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "verification_service": Provide(provide_email_verification_service),
    }

    @post("/request", status_code=HTTP_201_CREATED)
    async def request_verification(
        self,
        data: EmailVerificationRequest,
        users_service: UserService,
        verification_service: EmailVerificationTokenService,
    ) -> dict[str, str]:
        """Request email verification for a user."""
        # Find user by email
        user = await users_service.get_one_or_none(email=data.email)
        if user is None:
            # Don't reveal if email exists for security
            return {"message": "If the email exists, a verification link has been sent"}

        if user.is_verified:
            return {"message": "Email is already verified"}

        # Create verification token
        token = await verification_service.create_verification_token(user_id=user.id, email=user.email)

        # Send verification email
        await email_service.send_verification_email(cast(UserProtocol, user), token)

        return {
            "message": "Verification email sent",
            "token": token.token,  # Remove this in production - only for testing
        }

    @post("/verify", status_code=HTTP_200_OK)
    async def verify_email(
        self,
        data: EmailVerificationConfirm,
        users_service: UserService,
        verification_service: EmailVerificationTokenService,
    ) -> User:
        """Verify email using verification token."""
        # Verify the token
        verification_token = await verification_service.verify_token(data.token)

        # Mark user's email as verified
        user = await users_service.verify_email(user_id=verification_token.user_id, email=verification_token.email)

        return users_service.to_schema(user, schema_type=User)

    @get("/status/{user_id:uuid}")
    async def get_verification_status(
        self,
        user_id: UUID,
        users_service: UserService,
    ) -> dict[str, bool]:
        """Get email verification status for a user."""
        is_verified = await users_service.is_email_verified(user_id)
        return {"is_verified": is_verified}
