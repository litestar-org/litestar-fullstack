"""Persistence adapter for ``litestar-security`` WebAuthn passkeys and ceremony challenges."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import IntegrityError
from litestar_security.accounts import (
    LoginMethod,
    PasskeyAssertionStatus,
    PasskeyCredential,
    SecurityEvent,
    WebAuthnChallenge,
)

from app.db import models as m
from app.domain.accounts.security._event import security_audit_record
from app.domain.accounts.services import (
    PasskeyChallengeService,
    PasskeyService,
    PasskeyServices,
    UserService,
    is_constraint_violation,
)

if TYPE_CHECKING:
    from datetime import datetime

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

__all__ = ("SQLAlchemyPasskeyStore",)


class SQLAlchemyPasskeyStore:
    """Adapter implementing both ``PasskeyStore`` and ``WebAuthnChallengeStore`` on Advanced Alchemy services."""

    __slots__ = ("_alchemy_config",)

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the passkey and WebAuthn challenge store."""
        self._alchemy_config = alchemy_config

    async def add_credential(
        self,
        credential: PasskeyCredential,
        *,
        login_method: LoginMethod,
        event: SecurityEvent,
    ) -> bool:
        """Persist a new passkey credential, its login method, and its audit event in one transaction.

        Returns:
            ``True`` if stored, ``False`` if ``account_id`` is invalid or the credential already exists.

        Raises:
            IntegrityError: If the database fails for a reason other than a violated constraint.
        """
        if UserService.to_user_id(credential.account_id) is None:
            return False
        async with PasskeyServices.new(config=self._alchemy_config) as services:
            try:
                await services.passkeys.create(credential)
                await services.login_methods.record(credential.account_id, login_method)
                await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            except IntegrityError as error:
                if not is_constraint_violation(error):
                    raise
                return False
        return True

    async def get_credential(self, credential_id: bytes) -> PasskeyCredential | None:
        """Load one passkey credential by raw credential identifier bytes.

        Returns:
            Matching passkey credential, or ``None`` if not found.
        """
        async with PasskeyService.new(config=self._alchemy_config) as passkeys:
            passkey = await passkeys.get_one_or_none(m.UserPasskey.credential_id == credential_id.hex())
            return passkeys.to_credential(passkey) if passkey is not None else None

    async def list_credentials(self, account_id: str) -> tuple[PasskeyCredential, ...]:
        """List all passkey credentials owned by an account.

        Returns:
            Tuple of passkey credentials registered to ``account_id``.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return ()
        async with PasskeyService.new(config=self._alchemy_config) as passkeys:
            return tuple(
                passkeys.to_credential(passkey) for passkey in await passkeys.list(m.UserPasskey.user_id == user_id)
            )

    async def record_assertion(
        self,
        credential_id: bytes,
        *,
        expected_version: int,
        sign_count: int,
        backup_eligible: bool,
        backup_state: bool,
        clone_risk: bool,
        now: datetime,
    ) -> PasskeyAssertionStatus:
        """Optimistically update credential sign count, version, and clone-risk flag.

        Returns:
            Assertion recording status (``RECORDED``, ``CLONE_RISK``, or ``CONFLICT``).
        """
        async with PasskeyService.new(config=self._alchemy_config) as passkeys:
            passkey = await passkeys.get_one_or_none(m.UserPasskey.credential_id == credential_id.hex())
            if passkey is None:
                return PasskeyAssertionStatus.CONFLICT
            recorded = await passkeys.record_assertion(
                passkey,
                expected_version=expected_version,
                sign_count=sign_count,
                backup_eligible=backup_eligible,
                backup_state=backup_state,
                clone_risk=clone_risk,
                now=now,
            )
            await passkeys.repository.session.commit()
        if not recorded:
            return PasskeyAssertionStatus.CONFLICT
        return PasskeyAssertionStatus.CLONE_RISK if clone_risk else PasskeyAssertionStatus.RECORDED

    async def rename_credential(
        self,
        account_id: str,
        credential_id: bytes,
        display_name: str,
    ) -> PasskeyCredential | None:
        """Rename a passkey credential owned by the specified account.

        Returns:
            Updated passkey credential, or ``None`` if not found.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return None
        async with PasskeyService.new(config=self._alchemy_config) as passkeys:
            passkey = await passkeys.get_one_or_none(
                m.UserPasskey.user_id == user_id,
                m.UserPasskey.credential_id == credential_id.hex(),
            )
            if passkey is None:
                return None
            passkey.display_name = display_name
            return passkeys.to_credential(await passkeys.update(passkey, auto_commit=True))

    async def put(self, challenge: WebAuthnChallenge) -> None:
        """Persist a single-use WebAuthn ceremony challenge."""
        async with PasskeyChallengeService.new(config=self._alchemy_config) as passkey_challenges:
            await passkey_challenges.create(challenge, auto_commit=True)

    async def consume(
        self,
        challenge_digest: bytes,
        *,
        binding_digest: bytes,
        purpose: str,
        now: datetime,
    ) -> WebAuthnChallenge | None:
        """Atomically burn the WebAuthn challenge and return it only if binding, purpose, and expiry match.

        Returns:
            Consumed ``WebAuthnChallenge`` when all checks pass, otherwise ``None``.
        """
        async with PasskeyChallengeService.new(config=self._alchemy_config) as passkey_challenges:
            challenge = await passkey_challenges.redeem(
                challenge_digest,
                binding_digest=binding_digest,
                purpose=purpose,
                now=now,
            )
            await passkey_challenges.repository.session.commit()
        return challenge
