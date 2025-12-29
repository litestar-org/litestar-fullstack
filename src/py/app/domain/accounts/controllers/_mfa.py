"""MFA Management Controller."""

from __future__ import annotations

import base64
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import ClientException
from sqlalchemy.orm import undefer_group

from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.schemas import (
    MfaBackupCodes,
    MfaConfirm,
    MfaDisable,
    MfaSetup,
    MfaStatus,
)
from app.lib.crypt import (
    generate_backup_codes,
    generate_totp_qr_code,
    generate_totp_secret,
    get_totp_provisioning_uri,
    verify_password,
    verify_totp_code,
)
from app.lib.schema import Message

if TYPE_CHECKING:
    from litestar import Request
    from litestar.security.jwt import Token

    from app.db import models as m
    from app.domain.accounts.services import UserService

logger = logging.getLogger(__name__)


class MfaController(Controller):
    """MFA management endpoints for setting up and managing two-factor authentication."""

    tags = ["MFA"]
    path = "/api/mfa"
    dependencies = {
        "users_service": Provide(provide_users_service),
    }

    @get(operation_id="GetMfaStatus", path="/status")
    async def get_mfa_status(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
    ) -> MfaStatus:
        """Get current MFA status for the authenticated user.

        Args:
            request: Request with authenticated user

        Returns:
            Current MFA status
        """
        user = await users_service.get(request.user.id, load=[undefer_group("security_sensitive")])
        backup_codes_remaining = None

        if user.backup_codes:
            backup_codes_remaining = sum(1 for code in user.backup_codes if code)

        return MfaStatus(
            enabled=user.is_two_factor_enabled,
            confirmed_at=user.two_factor_confirmed_at,
            backup_codes_remaining=backup_codes_remaining,
        )

    @post(operation_id="InitiateMfaSetup", path="/enable")
    async def initiate_setup(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
    ) -> MfaSetup:
        """Initiate MFA setup - generates TOTP secret and QR code.

        The secret is stored but MFA is not enabled until confirmed with a valid code.

        Args:
            request: Request with authenticated user
            users_service: User service

        Returns:
            TOTP secret and QR code for authenticator app

        Raises:
            ClientException: If MFA is already enabled
        """
        user = await users_service.get(request.user.id, load=[undefer_group("security_sensitive")])

        if user.is_two_factor_enabled:
            raise ClientException(detail="MFA is already enabled", status_code=400)

        secret = generate_totp_secret()

        await users_service.update({"totp_secret": secret}, item_id=user.id)

        qr_code_bytes = generate_totp_qr_code(secret, user.email, issuer="Litestar App")
        qr_code_base64 = base64.b64encode(qr_code_bytes).decode("utf-8")

        provisioning_uri = get_totp_provisioning_uri(secret, user.email, issuer="Litestar App")

        return MfaSetup(
            secret=secret,
            qr_code=f"data:image/png;base64,{qr_code_base64}",
            provisioning_uri=provisioning_uri,
        )

    @post(operation_id="ConfirmMfaSetup", path="/confirm")
    async def confirm_setup(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        data: MfaConfirm,
    ) -> MfaBackupCodes:
        """Confirm MFA setup with a valid TOTP code.

        Verifies the code, enables MFA, and returns backup codes.

        Args:
            request: Request with authenticated user
            users_service: User service
            data: TOTP code from authenticator app

        Returns:
            Backup recovery codes (shown only once)

        Raises:
            ClientException: If code is invalid or no setup in progress
        """
        user = await users_service.get(request.user.id, load=[undefer_group("security_sensitive")])

        if user.is_two_factor_enabled:
            raise ClientException(detail="MFA is already enabled", status_code=400)

        if not user.totp_secret:
            raise ClientException(detail="No MFA setup in progress. Call /enable first.", status_code=400)

        if not verify_totp_code(user.totp_secret, data.code):
            raise ClientException(detail="Invalid verification code", status_code=400)

        plaintext_codes = generate_backup_codes(count=8)

        await users_service.update(
            {
                "is_two_factor_enabled": True,
                "two_factor_confirmed_at": datetime.now(UTC),
                "backup_codes": plaintext_codes,
            },
            item_id=user.id,
        )

        logger.info("MFA enabled for user %s", user.email)

        return MfaBackupCodes(codes=plaintext_codes)

    @delete(operation_id="DisableMfa", path="/disable", status_code=200)
    async def disable_mfa(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        data: MfaDisable,
    ) -> Message:
        """Disable MFA for the authenticated user.

        Requires password verification for security.

        Args:
            request: Request with authenticated user
            users_service: User service
            data: Password for verification

        Returns:
            Success message

        Raises:
            ClientException: If password is incorrect or MFA not enabled
        """
        user = await users_service.get(request.user.id, load=[undefer_group("security_sensitive")])

        if not user.is_two_factor_enabled:
            raise ClientException(detail="MFA is not enabled", status_code=400)

        if not user.hashed_password or not await verify_password(data.password, user.hashed_password):
            raise ClientException(detail="Invalid password", status_code=400)

        await users_service.update(
            {
                "is_two_factor_enabled": False,
                "totp_secret": None,
                "two_factor_confirmed_at": None,
                "backup_codes": None,
            },
            item_id=user.id,
        )

        logger.info("MFA disabled for user %s", user.email)

        return Message(message="MFA has been disabled")

    @post(operation_id="RegenerateMfaBackupCodes", path="/regenerate-codes")
    async def regenerate_backup_codes(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        data: MfaDisable,
    ) -> MfaBackupCodes:
        """Generate new backup codes (invalidates old ones).

        Requires password verification for security.

        Args:
            request: Request with authenticated user
            users_service: User service
            data: Password for verification

        Returns:
            New backup codes (shown only once)

        Raises:
            ClientException: If password is incorrect or MFA not enabled
        """
        user = await users_service.get(request.user.id, load=[undefer_group("security_sensitive")])

        if not user.is_two_factor_enabled:
            raise ClientException(detail="MFA is not enabled", status_code=400)

        if not user.hashed_password or not await verify_password(data.password, user.hashed_password):
            raise ClientException(detail="Invalid password", status_code=400)

        plaintext_codes = generate_backup_codes(count=8)

        await users_service.update({"backup_codes": plaintext_codes}, item_id=user.id)

        logger.info("Backup codes regenerated for user %s", user.email)

        return MfaBackupCodes(codes=plaintext_codes)
