"""MFA Challenge Controller for login verification."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from litestar import Controller, Response, post
from litestar.di import Provide
from litestar.exceptions import ClientException, NotAuthorizedException
from litestar.security.jwt import Token as JWTToken
from sqlalchemy.orm import undefer_group

from app.domain.accounts.deps import provide_refresh_token_service, provide_users_service
from app.domain.accounts.guards import auth
from app.domain.admin.deps import provide_audit_log_service
from app.lib.crypt import verify_backup_code, verify_totp_code

if TYPE_CHECKING:
    from uuid import UUID

    from litestar import Request
    from litestar.security.jwt import OAuth2Login, Token

    from app.db import models as m
    from app.domain.accounts.schemas import MfaChallenge
    from app.domain.accounts.services import RefreshTokenService, UserService
    from app.domain.admin.services import AuditLogService
    from app.lib.settings import AppSettings

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60
LOW_BACKUP_CODE_THRESHOLD = 2
MFA_RATE_LIMIT_WINDOW_MINUTES = 15
MFA_RATE_LIMIT_MAX_ATTEMPTS = 5

logger = logging.getLogger(__name__)


class MfaChallengeController(Controller):
    """MFA challenge verification during login flow."""

    tags = ["MFA"]
    path = "/api/mfa/challenge"
    dependencies = {
        "users_service": Provide(provide_users_service),
        "refresh_token_service": Provide(provide_refresh_token_service),
        "audit_service": Provide(provide_audit_log_service),
    }

    @post(operation_id="VerifyMfaChallenge", path="/verify", exclude_from_auth=True, security=[])
    async def verify_challenge(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        refresh_token_service: RefreshTokenService,
        audit_service: AuditLogService,
        settings: AppSettings,
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
            audit_service: Audit log service
            settings: Application settings
            data: TOTP code or backup code

        Returns:
            Full OAuth2 login response with access token

        Raises:
            NotAuthorizedException: If challenge token is invalid or code verification fails
        """

        mfa_token = request.cookies.get("mfa_challenge")
        if not mfa_token:
            raise NotAuthorizedException(detail="No MFA challenge in progress")

        user_email, user_id = self._decode_mfa_challenge_token(mfa_token, settings)
        user = await self._load_mfa_user(users_service, user_email, user_id)
        await self._enforce_rate_limit(audit_service, user.id)
        used_backup_code, _ = await self._verify_challenge_code(
            data=data,
            user=user,
            users_service=users_service,
            audit_service=audit_service,
            request=request,
        )

        await audit_service.log_action(
            action="mfa.challenge.success",
            actor_id=user.id,
            actor_email=user.email,
            target_type="user",
            target_id=str(user.id),
            details={"used_backup_code": used_backup_code},
            request=request,
        )

        device_info = request.headers.get("user-agent", "")[:255] if request.headers.get("user-agent") else None

        raw_refresh_token, _ = await refresh_token_service.create_refresh_token(
            user_id=user.id,
            device_info=device_info,
        )

        token_extras = {
            "user_id": str(user.id),
            "is_superuser": users_service.is_superuser(user),
            "is_verified": user.is_verified,
            "auth_method": "mfa",
            "amr": ["pwd", "mfa"],
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

        response.delete_cookie("mfa_challenge", path="/api/mfa")

        return response

    def _decode_mfa_challenge_token(self, token: str, settings: AppSettings) -> tuple[str, str]:
        try:
            decoded = JWTToken.decode(
                encoded_token=token,
                secret=settings.SECRET_KEY,
                algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
            )
        except Exception as exc:
            logger.warning("Failed to decode MFA challenge token: %s", exc)
            raise NotAuthorizedException(detail="Invalid or expired challenge token") from exc

        if decoded.extras.get("type") != "mfa_challenge":
            raise NotAuthorizedException(detail="Invalid challenge token")
        if decoded.aud != "mfa_verification":
            raise NotAuthorizedException(detail="Invalid challenge token audience")

        user_email = decoded.sub
        user_id = decoded.extras.get("user_id")
        if not user_email or not user_id:
            raise NotAuthorizedException(detail="Invalid challenge token")
        return user_email, user_id

    async def _load_mfa_user(self, users_service: UserService, user_email: str, user_id: str) -> m.User:
        user = await users_service.get_one_or_none(email=user_email, load=[undefer_group("security_sensitive")])
        if not user or str(user.id) != user_id:
            raise NotAuthorizedException(detail="Invalid challenge token")
        if not user.is_two_factor_enabled or not user.totp_secret:
            raise NotAuthorizedException(detail="MFA is not enabled for this user")
        return user

    async def _enforce_rate_limit(self, audit_service: AuditLogService, user_id: UUID) -> None:
        failed_attempts = await audit_service.count_recent_actions(
            action="mfa.challenge.failed",
            actor_id=user_id,
            window_minutes=MFA_RATE_LIMIT_WINDOW_MINUTES,
        )
        if failed_attempts >= MFA_RATE_LIMIT_MAX_ATTEMPTS:
            raise ClientException(detail="Too many verification attempts. Please try again later.", status_code=429)

    async def _verify_challenge_code(
        self,
        *,
        data: MfaChallenge,
        user: m.User,
        users_service: UserService,
        audit_service: AuditLogService,
        request: Request[m.User, Token, Any],
    ) -> tuple[bool, int | None]:
        if data.code:
            totp_secret = user.totp_secret
            if not totp_secret:
                raise NotAuthorizedException(detail="MFA is not enabled for this user")
            if verify_totp_code(totp_secret, data.code):
                return False, None
            await audit_service.log_action(
                action="mfa.challenge.failed",
                actor_id=user.id,
                actor_email=user.email,
                target_type="user",
                target_id=str(user.id),
                request=request,
            )
            raise NotAuthorizedException(detail="Invalid verification code")

        if not data.recovery_code:
            raise NotAuthorizedException(detail="Verification failed")

        if not user.backup_codes:
            raise NotAuthorizedException(detail="No backup codes available")

        code_index = await verify_backup_code(data.recovery_code.upper(), user.backup_codes)
        if code_index is None:
            await audit_service.log_action(
                action="mfa.challenge.failed",
                actor_id=user.id,
                actor_email=user.email,
                target_type="user",
                target_id=str(user.id),
                request=request,
            )
            raise NotAuthorizedException(detail="Invalid backup code")

        updated_codes = user.backup_codes.copy()
        updated_codes[code_index] = None
        await users_service.update({"backup_codes": updated_codes}, item_id=user.id)

        remaining_backup_codes = sum(1 for code in updated_codes if code)
        if remaining_backup_codes <= LOW_BACKUP_CODE_THRESHOLD:
            logger.warning("User %s has only %d backup codes remaining", user.email, remaining_backup_codes)

        return True, remaining_backup_codes
