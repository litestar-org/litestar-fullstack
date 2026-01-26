"""User Access Controllers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Any
from uuid import uuid4

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, delete, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, NotAuthorizedException
from litestar.params import Body, Dependency, Parameter
from litestar.security.jwt import Token as JWTToken
from sqlalchemy.orm import selectinload

from app.db import models as m
from app.domain.accounts.deps import (
    provide_email_verification_service,
    provide_password_reset_service,
    provide_roles_service,
    provide_users_service,
)
from app.domain.accounts.guards import auth
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
    TokenRefresh,
    User,
)
from app.domain.accounts.services import RefreshTokenService
from app.lib.deps import create_service_dependencies
from app.lib.schema import Message
from app.lib.validation import PasswordValidationError, validate_password_strength

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination
    from litestar.security.jwt import OAuth2Login, Token

    from app.domain.accounts.services import (
        PasswordResetService,
        RoleService,
        UserService,
    )
    from app.lib.email import AppEmailService
    from app.lib.settings import AppSettings

logger = logging.getLogger(__name__)

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = create_service_dependencies(
        RefreshTokenService,
        key="refresh_token_service",
        load=[selectinload(m.RefreshToken.user)],
        error_messages={
            "duplicate_key": "Refresh token already exists.",
            "integrity": "Refresh token operation failed.",
        },
        filters={
            "pagination_type": "limit_offset",
            "pagination_size": 25,
            "created_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    ) | {
        "users_service": Provide(provide_users_service),
        "roles_service": Provide(provide_roles_service),
        "verification_service": Provide(provide_email_verification_service),
        "password_reset_service": Provide(provide_password_reset_service),
    }

    @post(operation_id="AccountLogin", path="/api/access/login", exclude_from_auth=True, security=[])
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
            settings: Application settings

        Returns:
            OAuth2 Login Response with refresh token cookie, or MFA challenge
        """
        user = await users_service.authenticate(data.username, data.password)

        if user.is_two_factor_enabled and user.totp_secret:
            mfa_challenge_token = JWTToken(
                sub=user.email,
                exp=datetime.now(UTC) + timedelta(minutes=5),
                aud="mfa_verification",
                extras={
                    "type": "mfa_challenge",
                    "user_id": str(user.id),
                },
            )
            encoded_challenge = mfa_challenge_token.encode(
                secret=settings.SECRET_KEY,
                algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
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
                secure=settings.COOKIE_SECURE,
                samesite="lax",
                path="/api/mfa",
            )
            return response

        device_info = request.headers.get("user-agent", "")[:255] if request.headers.get("user-agent") else None

        raw_refresh_token, _ = await refresh_token_service.create_refresh_token(
            user_id=user.id,
            device_info=device_info,
        )

        token_extras = {
            "user_id": str(user.id),
            "is_superuser": users_service.is_superuser(user),
            "is_verified": user.is_verified,
            "auth_method": "password",
            "amr": ["pwd"],
        }
        response = auth.login(
            user.email,
            token_unique_jwt_id=str(uuid4()),
            token_extras=token_extras,
        )

        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=raw_refresh_token,
            max_age=REFRESH_TOKEN_MAX_AGE,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="strict",
            path="/api/access",
        )

        return response

    @post(operation_id="AccountLogout", path="/api/access/logout", exclude_from_auth=True, security=[])
    async def logout(
        self,
        request: Request[m.User, Token, Any],
        refresh_token_service: RefreshTokenService,
    ) -> Response[Message]:
        """Account Logout.

        Revokes the current refresh token family and clears cookies.

        Args:
            request: Request
            refresh_token_service: Refresh Token Service

        Returns:
            Logout Response
        """
        if raw_refresh_token := request.cookies.get(REFRESH_COOKIE_NAME):
            token_hash = refresh_token_service.hash_token(raw_refresh_token)
            if refresh_token := await refresh_token_service.get_one_or_none(token_hash=token_hash):
                await refresh_token_service.revoke_token_family(refresh_token.family_id)

        request.cookies.pop(auth.key, None)
        request.clear_session()
        response = Response(Message(message="OK"), status_code=200)
        response.delete_cookie(auth.key)
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/access")
        return response

    @post(operation_id="TokenRefresh", path="/api/access/refresh", exclude_from_auth=True, security=[])
    async def refresh_token(
        self,
        request: Request[m.User, Token, Any],
        refresh_token_service: RefreshTokenService,
        users_service: UserService,
        settings: AppSettings,
    ) -> Response[TokenRefresh]:
        """Refresh access token using refresh token.

        Implements token rotation - the old refresh token is revoked
        and a new one is issued.

        Args:
            request: Request with refresh token cookie
            refresh_token_service: Refresh Token Service
            users_service: User Service
            settings: Application settings

        Returns:
            New access token with rotated refresh token

        Raises:
            NotAuthorizedException: If refresh token is invalid or expired
        """
        if not (raw_refresh_token := request.cookies.get(REFRESH_COOKIE_NAME)):
            raise NotAuthorizedException(detail="No refresh token provided")

        device_info = request.headers.get("user-agent", "")[:255] if request.headers.get("user-agent") else None

        new_raw_token, new_token_model = await refresh_token_service.rotate_refresh_token(
            raw_token=raw_refresh_token,
            device_info=device_info,
        )

        user = await users_service.get(new_token_model.user_id)
        token_extras = {
            "user_id": str(user.id),
            "is_superuser": users_service.is_superuser(user),
            "is_verified": user.is_verified,
            "auth_method": "refresh",
            "amr": ["refresh"],
        }
        response = auth.login(
            user.email,
            token_unique_jwt_id=str(uuid4()),
            token_extras=token_extras,
        )

        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=new_raw_token,
            max_age=REFRESH_TOKEN_MAX_AGE,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="strict",
            path="/api/access",
        )

        return response

    @get(operation_id="GetActiveSessions", path="/api/access/sessions")
    async def get_sessions(
        self,
        request: Request[m.User, Token, Any],
        refresh_token_service: RefreshTokenService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[ActiveSession]:
        """Get all active sessions for the current user.

        Args:
            request: Request with authenticated user
            refresh_token_service: Refresh Token Service
            filters: Filter and pagination parameters

        Returns:
            Paginated active sessions
        """
        current_token_hash = None
        if raw_refresh_token := request.cookies.get(REFRESH_COOKIE_NAME):
            current_token_hash = refresh_token_service.hash_token(raw_refresh_token)
        active_tokens, total = await refresh_token_service.list_and_count(
            *filters,
            m.RefreshToken.user_id == request.user.id,
            m.RefreshToken.revoked_at.is_(None),
            m.RefreshToken.expires_at > datetime.now(UTC),
        )

        items = [
            {
                "id": token.id,
                "device_info": token.device_info,
                "created_at": token.created_at,
                "expires_at": token.expires_at,
                "is_current": token.token_hash == current_token_hash,
            }
            for token in active_tokens
        ]
        return refresh_token_service.to_schema(items, total, filters, schema_type=ActiveSession)

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
            ClientException: If session not found or does not belong to user
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
        if raw_refresh_token := request.cookies.get(REFRESH_COOKIE_NAME):
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
        data: AccountRegister,
        app_mailer: AppEmailService,
    ) -> User:
        """User Signup.

        Args:
            request: Request
            users_service: User Service
            roles_service: Role Service
            data: Account Register Data
            app_mailer: Email service for sending notifications

        Returns:
            User
        """
        user_data = data.to_dict()

        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))

        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})

        user = await users_service.create(user_data)
        request.app.emit(event_id="user_created", user_id=user.id, mailer=app_mailer)
        return users_service.to_schema(user, schema_type=User)

    @post(operation_id="ForgotPassword", path="/api/access/forgot-password", exclude_from_auth=True, security=[])
    async def forgot_password(
        self,
        users_service: UserService,
        password_reset_service: PasswordResetService,
        app_mailer: AppEmailService,
        request: Request[m.User, Token, Any],
        data: ForgotPasswordRequest,
    ) -> PasswordResetSent:
        """Initiate password reset flow.

        Args:
            data: Forgot password request data
            request: HTTP request object
            users_service: User service
            password_reset_service: Password reset service
            app_mailer: Email service for sending notifications

        Returns:
            Response indicating reset email status
        """
        user = await users_service.get_one_or_none(email=data.email)
        if user is None or not user.is_active:
            return PasswordResetSent(
                message="If the email exists, a password reset link has been sent", expires_in_minutes=60
            )
        if await password_reset_service.check_rate_limit(user.id):
            return PasswordResetSent(
                message="Too many password reset requests. Please try again later", expires_in_minutes=60
            )
        request.app.emit(event_id="password_reset_requested", user_id=user.id, mailer=app_mailer)
        return PasswordResetSent(
            message="If the email exists, a password reset link has been sent", expires_in_minutes=60
        )

    @get(operation_id="ValidateResetToken", path="/api/access/reset-password", exclude_from_auth=True, security=[])
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
        except ClientException:
            logger.warning("Failed to validate reset token", exc_info=True)

        return ResetTokenValidation(valid=False)

    @post(operation_id="ResetPassword", path="/api/access/reset-password", exclude_from_auth=True, security=[])
    async def reset_password_with_token(
        self,
        data: ResetPasswordRequest,
        users_service: UserService,
        password_reset_service: PasswordResetService,
        request: Request[m.User, Token, Any],
        app_mailer: AppEmailService,
    ) -> PasswordResetComplete:
        """Complete password reset with token.

        Args:
            data: Password reset request data
            users_service: User service
            password_reset_service: Password reset service
            request: HTTP request object
            app_mailer: Email service for sending notifications

        Returns:
            Password reset confirmation

        Raises:
            ClientException: If token is invalid or passwords do not match
        """

        if data.password != data.password_confirm:
            raise ClientException(detail="Passwords do not match", status_code=400)

        try:
            validate_password_strength(data.password)
        except PasswordValidationError as e:
            raise ClientException(detail=str(e), status_code=400) from e
        reset_token = await password_reset_service.use_reset_token(data.token)
        user = await users_service.reset_password_with_token(user_id=reset_token.user_id, new_password=data.password)
        request.app.emit(event_id="password_reset_completed", user_id=user.id, mailer=app_mailer)
        return PasswordResetComplete(message="Password has been successfully reset", user_id=user.id)
