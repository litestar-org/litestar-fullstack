"""MFA Challenge Controller for login verification."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from litestar import Controller, Response, post
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException

from app.domain.accounts.dependencies import provide_refresh_token_service, provide_users_service
from app.lib.crypt import verify_backup_code, verify_totp_code
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from litestar import Request
    from litestar.security.jwt import OAuth2Login, Token

    from app.db import models as m
    from app.domain.accounts.schemas import MfaChallenge
    from app.domain.accounts.services import RefreshTokenService, UserService

settings = get_settings()

# Refresh token cookie configuration (shared with _access.py)
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"  # noqa: S105 - This is a cookie name, not a password
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


logger = logging.getLogger(__name__)


class MfaChallengeController(Controller):
    """MFA challenge verification during login flow."""

    tags = ["MFA"]
    path = "/api/mfa/challenge"
    dependencies = {
        "users_service": Provide(provide_users_service),
        "refresh_token_service": Provide(provide_refresh_token_service),
    }

    @post(operation_id="VerifyMfaChallenge", path="/verify", exclude_from_auth=True)
    async def verify_challenge(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        refresh_token_service: RefreshTokenService,
        data: MfaChallenge,
    ) -> Response[OAuth2Login]:
        """Verify MFA code during login flow.

        This endpoint is called after initial password authentication
        when MFA is enabled. It accepts either a TOTP code or a backup code.

        The MFA challenge token should be in the request cookies,
        set during the initial login step.

        Args:
            request: Request containing MFA challenge token
            users_service: User service
            refresh_token_service: Refresh token service for issuing tokens
            data: TOTP code or backup code

        Returns:
            Full OAuth2 login response with access token

        Raises:
            NotAuthorizedException: If challenge token is invalid or code verification fails
        """
        from app.domain.accounts.guards import auth

        # Get the MFA challenge token from cookies
        mfa_token = request.cookies.get("mfa_challenge")
        if not mfa_token:
            raise NotAuthorizedException(detail="No MFA challenge in progress")

        # Decode and validate the challenge token
        try:
            from litestar.security.jwt import Token as JWTToken

            decoded = JWTToken.decode(
                encoded_token=mfa_token,
                secret=settings.app.SECRET_KEY,
                algorithm=settings.app.JWT_ENCRYPTION_ALGORITHM,
            )
        except Exception as e:
            logger.warning("Failed to decode MFA challenge token: %s", e)
            raise NotAuthorizedException(detail="Invalid or expired challenge token") from e

        # Verify this is an MFA challenge token
        if decoded.extras.get("type") != "mfa_challenge":
            raise NotAuthorizedException(detail="Invalid challenge token")

        user_email = decoded.sub
        user_id = decoded.extras.get("user_id")

        # Get the user
        user = await users_service.get_one_or_none(email=user_email)
        if not user or str(user.id) != user_id:
            raise NotAuthorizedException(detail="Invalid challenge token")

        if not user.is_two_factor_enabled or not user.totp_secret:
            raise NotAuthorizedException(detail="MFA is not enabled for this user")

        verified = False
        used_backup_code = False
        remaining_backup_codes = None

        # Verify TOTP code
        if data.code:
            verified = verify_totp_code(user.totp_secret, data.code)
            if not verified:
                raise NotAuthorizedException(detail="Invalid verification code")

        # Verify backup code
        elif data.recovery_code:
            if not user.backup_codes:
                raise NotAuthorizedException(detail="No backup codes available")

            code_index = await verify_backup_code(data.recovery_code.upper(), user.backup_codes)
            if code_index is None:
                raise NotAuthorizedException(detail="Invalid backup code")

            verified = True
            used_backup_code = True

            # Invalidate the used backup code
            updated_codes = user.backup_codes.copy()
            updated_codes[code_index] = None  # Mark as used
            await users_service.update({"backup_codes": updated_codes}, item_id=user.id)

            remaining_backup_codes = sum(1 for code in updated_codes if code)

            if remaining_backup_codes <= 2:  # noqa: PLR2004
                logger.warning("User %s has only %d backup codes remaining", user.email, remaining_backup_codes)

        if not verified:
            raise NotAuthorizedException(detail="Verification failed")

        logger.info(
            "MFA verification successful for user %s (backup_code=%s)",
            user.email,
            used_backup_code,
        )

        # Get device info from user agent
        device_info = request.headers.get("user-agent", "")[:255] if request.headers.get("user-agent") else None

        # Create refresh token (new family for MFA-verified login)
        raw_refresh_token, _ = await refresh_token_service.create_refresh_token(
            user_id=user.id,
            device_info=device_info,
        )

        # Issue full auth tokens
        response = auth.login(user.email)

        # Add refresh token as HTTP-only cookie
        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=raw_refresh_token,
            max_age=REFRESH_TOKEN_MAX_AGE,
            httponly=True,
            secure=settings.app.CSRF_COOKIE_SECURE,
            samesite="lax",
            path="/api/access",
        )

        # Clear the MFA challenge cookie
        response.delete_cookie("mfa_challenge", path="/api/mfa")

        return response
