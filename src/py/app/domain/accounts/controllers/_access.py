"""User Access Controllers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, cast

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, delete, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, NotAuthorizedException
from litestar.params import Body, Parameter

from app.domain.accounts.dependencies import (
    provide_email_verification_service,
    provide_password_reset_service,
    provide_refresh_token_service,
    provide_roles_service,
    provide_users_service,
)
from app.domain.accounts.schemas import (
    AccountLogin,
    AccountRegister,
    ActiveSession,
    ForgotPasswordRequest,
    LoginMfaChallenge,
    PasswordResetComplete,
    PasswordResetSent,
    ResetPasswordRequest,
    ResetTokenValidation,
    SessionList,
    TokenRefresh,
    User,
)
from app.lib.email import email_service
from app.lib.settings import AppSettings
from app.lib.validation import PasswordValidationError, validate_password_strength
from app.schemas.base import Message

if TYPE_CHECKING:
    from uuid import UUID

    from litestar.security.jwt import OAuth2Login, Token

    from app.db import models as m
    from app.domain.accounts.services import (
        EmailVerificationTokenService,
        PasswordResetService,
        RefreshTokenService,
        RoleService,
        UserService,
    )
    from app.lib.email.service import UserProtocol

logger = logging.getLogger(__name__)

REFRESH_TOKEN_COOKIE_NAME = "refresh_token"  # noqa: S105
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "roles_service": Provide(provide_roles_service),
        "verification_service": Provide(provide_email_verification_service),
        "password_reset_service": Provide(provide_password_reset_service),
        "refresh_token_service": Provide(provide_refresh_token_service),
    }

    @post(operation_id="AccountLogin", path="/api/access/login", exclude_from_auth=True)
    async def login(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        refresh_token_service: RefreshTokenService,
        settings: AppSettings,
        data: Annotated[AccountLogin, Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response[OAuth2Login] | Response[LoginMfaChallenge]:
        """Authenticate a user.

        If MFA is enabled, returns a response indicating MFA is required
        with a challenge token in a cookie. Otherwise, returns full OAuth2 tokens.

        Args:
            request: The HTTP request
            data: OAuth2 Login Data
            users_service: User Service
            refresh_token_service: Refresh Token Service

        Returns:
            OAuth2 Login Response with refresh token cookie, or MFA challenge
        """
        from datetime import UTC, datetime, timedelta

        from litestar.security.jwt import Token as JWTToken

        from app.domain.accounts.guards import auth

        user = await users_service.authenticate(data.username, data.password)

        if user.is_two_factor_enabled and user.totp_secret:

            mfa_challenge_token = JWTToken(
                sub=user.email,
                exp=datetime.now(UTC) + timedelta(minutes=5),
                extras={
                    "type": "mfa_challenge",
                    "user_id": str(user.id),
                },
            )
            encoded_challenge = mfa_challenge_token.encode(
                secret=settings.app.SECRET_KEY,
                algorithm=settings.app.JWT_ENCRYPTION_ALGORITHM,
            )

            response = Response(
                LoginMfaChallenge(
                    mfa_required=True,
                    message="MFA verification required",
                ),
                status_code=200,
            )
            response.set_cookie(
                key="mfa_challenge",
                value=encoded_challenge,
                max_age=300,
                httponly=True,
                secure=settings.app.CSRF_COOKIE_SECURE,
                samesite="lax",
                path="/api/mfa",
            )
            return response

        device_info = request.headers.get("user-agent", "")[:255] if request.headers.get("user-agent") else None

        raw_refresh_token, _ = await refresh_token_service.create_refresh_token(
            user_id=user.id,
            device_info=device_info,
        )

        response = auth.login(user.email)

        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=raw_refresh_token,
            max_age=REFRESH_TOKEN_MAX_AGE,
            httponly=True,
            secure=settings.app.CSRF_COOKIE_SECURE,
            samesite="lax",
            path="/api/access",
        )

        return response

    @post(operation_id="AccountLogout", path="/api/access/logout", exclude_from_auth=True)
    async def logout(
        self,
        request: Request[m.User, Token, Any],
        refresh_token_service: RefreshTokenService,
    ) -> Response[Message]:
        """Account Logout

        Revokes the current refresh token family and clears cookies.

        Args:
            request: Request
            refresh_token_service: Refresh Token Service

        Returns:
            Logout Response
        """
        from app.domain.accounts.guards import auth

        raw_refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        if raw_refresh_token:
            try:
                token_hash = refresh_token_service.hash_token(raw_refresh_token)
                refresh_token = await refresh_token_service.get_one_or_none(token_hash=token_hash)
                if refresh_token:
                    await refresh_token_service.revoke_token_family(refresh_token.family_id)
            except Exception:  # noqa: BLE001, S110

                pass

        request.cookies.pop(auth.key, None)
        request.clear_session()
        response = Response(Message(message="OK"), status_code=200)
        response.delete_cookie(auth.key)
        response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, path="/api/access")
        return response

    @post(operation_id="TokenRefresh", path="/api/access/refresh", exclude_from_auth=True)
    async def refresh_token(
        self,
        request: Request[m.User, Token, Any],
        refresh_token_service: RefreshTokenService,
        settings: AppSettings,
    ) -> Response[TokenRefresh]:
        """Refresh access token using refresh token.

        Implements token rotation - the old refresh token is revoked
        and a new one is issued.

        Args:
            request: Request with refresh token cookie
            refresh_token_service: Refresh Token Service

        Returns:
            New access token with rotated refresh token

        Raises:
            NotAuthorizedException: If refresh token is invalid or expired
        """
        from app.domain.accounts.guards import auth

        raw_refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        if not raw_refresh_token:
            raise NotAuthorizedException(detail="No refresh token provided")

        device_info = request.headers.get("user-agent", "")[:255] if request.headers.get("user-agent") else None

        new_raw_token, new_token_model = await refresh_token_service.rotate_refresh_token(
            raw_token=raw_refresh_token,
            device_info=device_info,
        )

        response = auth.login(new_token_model.user.email)

        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=new_raw_token,
            max_age=REFRESH_TOKEN_MAX_AGE,
            httponly=True,
            secure=settings.app.CSRF_COOKIE_SECURE,
            samesite="lax",
            path="/api/access",
        )

        return response

    @get(operation_id="GetActiveSessions", path="/api/access/sessions")
    async def get_sessions(
        self,
        request: Request[m.User, Token, Any],
        refresh_token_service: RefreshTokenService,
    ) -> SessionList:
        """Get all active sessions for the current user.

        Args:
            request: Request with authenticated user
            refresh_token_service: Refresh Token Service

        Returns:
            List of active sessions
        """

        current_token_hash = None
        raw_refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        if raw_refresh_token:
            current_token_hash = refresh_token_service.hash_token(raw_refresh_token)

        active_tokens = await refresh_token_service.get_active_sessions(request.user.id)

        sessions = [
            ActiveSession(
                id=token.id,
                device_info=token.device_info,
                created_at=token.created_at,
                expires_at=token.expires_at,
                is_current=token.token_hash == current_token_hash,
            )
            for token in active_tokens
        ]

        return SessionList(sessions=sessions, count=len(sessions))

    @delete(operation_id="RevokeSession", path="/api/access/sessions/{session_id:uuid}", status_code=200)
    async def revoke_session(
        self,
        request: Request[m.User, Token, Any],
        refresh_token_service: RefreshTokenService,
        session_id: UUID,
    ) -> Message:
        """Revoke a specific session.

        Args:
            request: Request with authenticated user
            refresh_token_service: Refresh Token Service
            session_id: ID of the session to revoke

        Returns:
            Success message

        Raises:
            ClientException: If session not found or doesn't belong to user
        """

        token = await refresh_token_service.get_one_or_none(id=session_id)
        if not token or token.user_id != request.user.id:
            raise ClientException(detail="Session not found", status_code=404)

        await refresh_token_service.revoke_token_family(token.family_id)

        return Message(message="Session revoked successfully")

    @delete(operation_id="RevokeAllSessions", path="/api/access/sessions", status_code=200)
    async def revoke_all_sessions(
        self,
        request: Request[m.User, Token, Any],
        refresh_token_service: RefreshTokenService,
    ) -> Message:
        """Revoke all sessions except the current one.

        Args:
            request: Request with authenticated user
            refresh_token_service: Refresh Token Service

        Returns:
            Success message
        """

        current_token_hash = None
        raw_refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        if raw_refresh_token:
            current_token_hash = refresh_token_service.hash_token(raw_refresh_token)

        active_tokens = await refresh_token_service.get_active_sessions(request.user.id)

        revoked_count = 0
        for token in active_tokens:
            if token.token_hash != current_token_hash:
                revoked_count += await refresh_token_service.revoke_token_family(token.family_id)

        return Message(message=f"Revoked {revoked_count} session(s)")

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

        user_data["is_verified"] = False

        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})

        user = await users_service.create(user_data)
        request.app.emit(event_id="user_created", user_id=user.id)

        _, verification_token = await verification_service.create_verification_token(user_id=user.id, email=user.email)
        await email_service.send_verification_email(cast("UserProtocol", user), verification_token)

        return users_service.to_schema(user, schema_type=User)

    @post(operation_id="ForgotPassword", path="/api/access/forgot-password", exclude_from_auth=True)
    async def forgot_password(
        self,
        data: ForgotPasswordRequest,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        password_reset_service: PasswordResetService,
    ) -> PasswordResetSent:
        """Initiate password reset flow.

        Args:
            data: Forgot password request data
            request: HTTP request object
            users_service: User service
            password_reset_service: Password reset service

        Returns:
            Response indicating reset email status
        """

        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        user = await users_service.get_one_or_none(email=data.email)

        if user is None or not user.is_active:
            return PasswordResetSent(
                message="If the email exists, a password reset link has been sent", expires_in_minutes=60
            )

        if await password_reset_service.check_rate_limit(user.id):
            return PasswordResetSent(
                message="Too many password reset requests. Please try again later", expires_in_minutes=60
            )

        _, reset_token = await password_reset_service.create_reset_token(
            user_id=user.id, ip_address=ip_address, user_agent=user_agent
        )

        await email_service.send_password_reset_email(
            user=cast("UserProtocol", user),
            reset_token=reset_token,
            expires_in_minutes=60,
            ip_address=ip_address,
        )

        return PasswordResetSent(
            message="If the email exists, a password reset link has been sent", expires_in_minutes=60
        )

    @get(operation_id="ValidateResetToken", path="/api/access/reset-password", exclude_from_auth=True)
    async def validate_reset_token(
        self,
        token: Annotated[str, Parameter(query="token", min_length=32, max_length=255)],
        password_reset_service: PasswordResetService,
    ) -> ResetTokenValidation:
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
                return ResetTokenValidation(
                    valid=True, user_id=reset_token.user_id, expires_at=reset_token.expires_at.isoformat()
                )
        except Exception:  # noqa: BLE001
            logger.warning("Failed to validate reset token", exc_info=True)

        return ResetTokenValidation(valid=False)

    @post(operation_id="ResetPassword", path="/api/access/reset-password", exclude_from_auth=True)
    async def reset_password_with_token(
        self,
        data: ResetPasswordRequest,
        users_service: UserService,
        password_reset_service: PasswordResetService,
    ) -> PasswordResetComplete:
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

        if data.password != data.password_confirm:
            raise ClientException(detail="Passwords do not match", status_code=400)

        try:
            validate_password_strength(data.password)
        except PasswordValidationError as e:
            raise ClientException(detail=str(e), status_code=400) from e

        reset_token = await password_reset_service.use_reset_token(data.token)

        user = await users_service.reset_password_with_token(user_id=reset_token.user_id, new_password=data.password)

        await email_service.send_password_reset_confirmation_email(cast("UserProtocol", user))

        return PasswordResetComplete(message="Password has been successfully reset", user_id=user.id)
