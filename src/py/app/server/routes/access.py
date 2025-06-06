"""User Access Controllers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body, Parameter

from app import schemas as s
from app.lib.deps import create_service_provider
from app.lib.email import email_service
from app.lib.validation import PasswordValidationError, validate_password_strength
from app.server import deps, security
from app.services import RoleService, UserService

if TYPE_CHECKING:
    from litestar.security.jwt import OAuth2Login, Token

    from app.db import models as m
    from app.services._email_verification import EmailVerificationTokenService
    from app.services._password_reset import PasswordResetService


logger = logging.getLogger(__name__)


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {
        "users_service": Provide(deps.provide_users_service),
        "roles_service": Provide(create_service_provider(RoleService)),
        "verification_service": Provide(deps.provide_email_verification_service),
        "password_reset_service": Provide(deps.provide_password_reset_service),
    }

    @post(operation_id="AccountLogin", path="/api/access/login", exclude_from_auth=True)
    async def login(
        self,
        users_service: UserService,
        data: Annotated[s.AccountLogin, Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response[OAuth2Login]:
        """Authenticate a user.

        Args:
            data: OAuth2 Login Data
            users_service: User Service

        Returns:
            OAuth2 Login Response
        """
        user = await users_service.authenticate(data.username, data.password)
        return security.auth.login(user.email)

    @post(operation_id="AccountLogout", path="/api/access/logout", exclude_from_auth=True)
    async def logout(self, request: Request[m.User, Token, Any]) -> Response[s.Message]:
        """Account Logout

        Args:
            request: Request

        Returns:
            Logout Response
        """
        request.cookies.pop(security.auth.key, None)
        request.clear_session()
        response = Response(s.Message(message="OK"), status_code=200)
        response.delete_cookie(security.auth.key)
        return response

    @post(operation_id="AccountRegister", path="/api/access/signup")
    async def signup(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        roles_service: RoleService,
        verification_service: EmailVerificationTokenService,
        data: s.AccountRegister,
    ) -> s.User:
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
        await email_service.send_verification_email(user, verification_token)

        return users_service.to_schema(user, schema_type=s.User)

    @post(operation_id="ForgotPassword", path="/api/access/forgot-password", exclude_from_auth=True)
    async def forgot_password(
        self,
        data: s.ForgotPasswordRequest,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        password_reset_service: PasswordResetService,
    ) -> s.ForgotPasswordResponse:
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
            return s.ForgotPasswordResponse(
                message="If the email exists, a password reset link has been sent", expires_in_minutes=60
            )

        # Check rate limiting
        if await password_reset_service.check_rate_limit(user.id):
            return s.ForgotPasswordResponse(
                message="Too many password reset requests. Please try again later", expires_in_minutes=60
            )

        # Create reset token
        reset_token = await password_reset_service.create_reset_token(
            user_id=user.id, ip_address=ip_address, user_agent=user_agent
        )

        # Send reset email
        await email_service.send_password_reset_email(
            user=user, reset_token=reset_token, expires_in_minutes=60, ip_address=ip_address
        )

        return s.ForgotPasswordResponse(
            message="If the email exists, a password reset link has been sent", expires_in_minutes=60
        )

    @get(operation_id="ValidateResetToken", path="/api/access/reset-password", exclude_from_auth=True)
    async def validate_reset_token(
        self,
        token: Annotated[str, Parameter(query="token", min_length=32, max_length=255)],
        password_reset_service: PasswordResetService,
    ) -> s.ValidateResetTokenResponse:
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
                return s.ValidateResetTokenResponse(
                    valid=True, user_id=reset_token.user_id, expires_at=reset_token.expires_at.isoformat()
                )
        except Exception:
            logger.warning("Failed to validate reset token: %s", token, exc_info=True)

        return s.ValidateResetTokenResponse(valid=False)

    @post(operation_id="ResetPassword", path="/api/access/reset-password", exclude_from_auth=True)
    async def reset_password_with_token(
        self,
        data: s.ResetPasswordRequest,
        users_service: UserService,
        password_reset_service: PasswordResetService,
    ) -> s.ResetPasswordResponse:
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
        # TODO: Implement with a proper Litestar exception handler
        try:
            validate_password_strength(data.password)
        except PasswordValidationError as e:
            raise ClientException(detail=str(e), status_code=400) from e

        # Use the reset token (validates and marks as used)
        reset_token = await password_reset_service.use_reset_token(data.token)

        # Reset the user's password
        user = await users_service.reset_password_with_token(user_id=reset_token.user_id, new_password=data.password)

        # Send confirmation email
        await email_service.send_password_reset_confirmation_email(user)

        return s.ResetPasswordResponse(message="Password has been successfully reset", user_id=user.id)
