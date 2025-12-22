"""User Access Controllers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, cast

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body, Parameter

from app.domain.accounts.dependencies import (
    provide_email_verification_service,
    provide_password_reset_service,
    provide_roles_service,
    provide_users_service,
)
from app.domain.accounts.schemas import (
    AccountLogin,
    AccountRegister,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    User,
    ValidateResetTokenResponse,
)
from app.lib.email import email_service
from app.lib.email.service import UserProtocol
from app.lib.validation import PasswordValidationError, validate_password_strength
from app.schemas.base import Message

if TYPE_CHECKING:
    from litestar.security.jwt import OAuth2Login, Token

    from app.db import models as m
    from app.domain.accounts.services import (
        EmailVerificationTokenService,
        PasswordResetService,
        RoleService,
        UserService,
    )


logger = logging.getLogger(__name__)


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "roles_service": Provide(provide_roles_service),
        "verification_service": Provide(provide_email_verification_service),
        "password_reset_service": Provide(provide_password_reset_service),
    }

    @post(operation_id="AccountLogin", path="/api/access/login", exclude_from_auth=True)
    async def login(
        self,
        users_service: UserService,
        data: Annotated[AccountLogin, Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response[OAuth2Login]:
        """Authenticate a user.

        Args:
            data: OAuth2 Login Data
            users_service: User Service

        Returns:
            OAuth2 Login Response
        """
        from app.domain.accounts.guards import auth

        user = await users_service.authenticate(data.username, data.password)
        return auth.login(user.email)

    @post(operation_id="AccountLogout", path="/api/access/logout", exclude_from_auth=True)
    async def logout(self, request: Request[m.User, Token, Any]) -> Response[Message]:
        """Account Logout

        Args:
            request: Request

        Returns:
            Logout Response
        """
        from app.domain.accounts.guards import auth

        request.cookies.pop(auth.key, None)
        request.clear_session()
        response = Response(Message(message="OK"), status_code=200)
        response.delete_cookie(auth.key)
        return response

    @post(operation_id="AccountRegister", path="/api/access/signup")
    async def signup(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        roles_service: RoleService,
        verification_service: EmailVerificationTokenService,
        data: AccountRegister,
    ) -> User:
        """User Signup.

        Args:
            request: Request
            users_service: User Service
            roles_service: Role Service
            verification_service: Email Verification Service
            data: Account Register Data

        Returns:
            User
        """
        user_data = data.to_dict()
        # Set is_verified to False for new registrations (require email verification)
        user_data["is_verified"] = False

        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})

        user = await users_service.create(user_data)
        request.app.emit(event_id="user_created", user_id=user.id)

        # Send verification email
        verification_token = await verification_service.create_verification_token(user_id=user.id, email=user.email)
        await email_service.send_verification_email(cast(UserProtocol, user), verification_token)

        return users_service.to_schema(user, schema_type=User)

    @post(operation_id="ForgotPassword", path="/api/access/forgot-password", exclude_from_auth=True)
    async def forgot_password(
        self,
        data: ForgotPasswordRequest,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        password_reset_service: PasswordResetService,
    ) -> ForgotPasswordResponse:
        """Initiate password reset flow.

        Args:
            data: Forgot password request data
            request: HTTP request object
            users_service: User service
            password_reset_service: Password reset service

        Returns:
            Response indicating reset email status
        """
        # Get client IP and user agent for security logging
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Find user by email
        user = await users_service.get_one_or_none(email=data.email)

        # For security, always return success message (don't reveal if email exists)
        if user is None or not user.is_active:
            return ForgotPasswordResponse(
                message="If the email exists, a password reset link has been sent", expires_in_minutes=60
            )

        # Check rate limiting
        if await password_reset_service.check_rate_limit(user.id):
            return ForgotPasswordResponse(
                message="Too many password reset requests. Please try again later", expires_in_minutes=60
            )

        # Create reset token
        reset_token = await password_reset_service.create_reset_token(
            user_id=user.id, ip_address=ip_address, user_agent=user_agent
        )

        # Send reset email
        await email_service.send_password_reset_email(
            user=cast(UserProtocol, user),
            reset_token=reset_token,
            expires_in_minutes=60,
            ip_address=ip_address,
        )

        return ForgotPasswordResponse(
            message="If the email exists, a password reset link has been sent", expires_in_minutes=60
        )

    @get(operation_id="ValidateResetToken", path="/api/access/reset-password", exclude_from_auth=True)
    async def validate_reset_token(
        self,
        token: Annotated[str, Parameter(query="token", min_length=32, max_length=255)],
        password_reset_service: PasswordResetService,
    ) -> ValidateResetTokenResponse:
        """Validate a password reset token.

        Args:
            token: Reset token from URL parameter
            password_reset_service: Password reset service

        Returns:
            Token validation response
        """
        try:
            reset_token = await password_reset_service.validate_reset_token(token)
            if reset_token:
                return ValidateResetTokenResponse(
                    valid=True, user_id=reset_token.user_id, expires_at=reset_token.expires_at.isoformat()
                )
        except Exception:  # noqa: BLE001 - Intentionally catching all exceptions to avoid leaking validation info
            logger.warning("Failed to validate reset token: %s", token, exc_info=True)

        return ValidateResetTokenResponse(valid=False)

    @post(operation_id="ResetPassword", path="/api/access/reset-password", exclude_from_auth=True)
    async def reset_password_with_token(
        self,
        data: ResetPasswordRequest,
        users_service: UserService,
        password_reset_service: PasswordResetService,
    ) -> ResetPasswordResponse:
        """Complete password reset with token.

        Args:
            data: Password reset request data
            request: HTTP request object
            users_service: User service
            password_reset_service: Password reset service

        Returns:
            Password reset confirmation

        Raises:
            ClientException: If token is invalid or passwords don't match
        """
        # Validate passwords match
        if data.password != data.password_confirm:
            raise ClientException(detail="Passwords do not match", status_code=400)

        # Validate password strength
        # Password validation errors are converted to ClientExceptions for consistent API responses
        try:
            validate_password_strength(data.password)
        except PasswordValidationError as e:
            raise ClientException(detail=str(e), status_code=400) from e

        # Use the reset token (validates and marks as used)
        reset_token = await password_reset_service.use_reset_token(data.token)

        # Reset the user's password
        user = await users_service.reset_password_with_token(user_id=reset_token.user_id, new_password=data.password)

        # Send confirmation email
        await email_service.send_password_reset_confirmation_email(cast(UserProtocol, user))

        return ResetPasswordResponse(message="Password has been successfully reset", user_id=user.id)
