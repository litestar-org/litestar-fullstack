"""Persistence adapters for ``litestar-security`` MFA, step-up grants, and login challenges."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar_security.accounts import (
    AESGCMSecretProtector,
    LoginMethod,
    MFALoginChallenge,
    PendingTOTPEnrollment,
    RecoveryCodeDigest,
    SecretProtectorKey,
    SecurityEvent,
    StepUpGrantState,
    TOTPMethod,
)

from app.domain.accounts.security.events import security_audit_record
from app.domain.accounts.services import (
    MFAFactorService,
    MFALoginChallengeService,
    MFARecoveryCodeService,
    MFAServices,
    StepUpGrantService,
    UserService,
)
from app.lib.secrets import TOTP_PROTECTOR_INFO, derive_subkey

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

    from app.lib.settings import Settings

__all__ = (
    "SQLAlchemyMFALoginChallengeService",
    "SQLAlchemyMFAService",
    "SQLAlchemyStepUpService",
    "build_secret_protector",
)


def build_secret_protector(
    settings: Settings,
    *,
    key_version: str = "v1",
    retained_keys: Sequence[SecretProtectorKey] = (),
) -> AESGCMSecretProtector:
    """Build an ``AESGCMSecretProtector`` backed by an HKDF-derived 32-byte key.

    Returns:
        Configured ``AESGCMSecretProtector`` instance.
    """
    active = SecretProtectorKey(
        key_version=key_version,
        key=derive_subkey(settings.app.SECRET_KEY, TOTP_PROTECTOR_INFO),
    )
    return AESGCMSecretProtector(active_key=active, retained_keys=tuple(retained_keys))


class SQLAlchemyMFAService:
    """Adapter implementing ``MFAStore`` for encrypted TOTP factors and peppered recovery code digests."""

    __slots__ = ("_alchemy_config",)

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the MFA store."""
        self._alchemy_config = alchemy_config

    async def create_totp_enrollment(self, enrollment: PendingTOTPEnrollment) -> None:
        """Persist a pending encrypted TOTP enrollment, rejecting a non-UUID ``account_id`` with ``ValueError``."""
        async with MFAFactorService.new(config=self._alchemy_config) as mfa_factors:
            await mfa_factors.create(enrollment, auto_commit=True)

    async def get_totp_enrollment(self, enrollment_id: str) -> PendingTOTPEnrollment | None:
        """Load a pending TOTP enrollment by identifier.

        Returns:
            Matching pending enrollment, or ``None`` if not found.
        """
        async with MFAFactorService.new(config=self._alchemy_config) as mfa_factors:
            mfa_factor = await mfa_factors.find_pending(enrollment_id)
            return mfa_factors.to_enrollment(mfa_factor) if mfa_factor is not None else None

    async def activate_totp(
        self,
        account_id: str,
        enrollment_id: str,
        *,
        accepted_counter: int,
        login_method: LoginMethod,
        event: SecurityEvent,
        now: datetime,
    ) -> TOTPMethod | None:
        """Confirm a pending TOTP enrollment, its login method, and its audit event in one transaction.

        Returns:
            Activated ``TOTPMethod``, or ``None`` if missing, expired, or already confirmed.
        """
        return await self._activate(
            account_id,
            enrollment_id,
            accepted_counter=accepted_counter,
            login_method=login_method,
            event=event,
            now=now,
            codes=None,
        )

    async def activate_totp_with_recovery_codes(
        self,
        account_id: str,
        enrollment_id: str,
        *,
        accepted_counter: int,
        codes: tuple[RecoveryCodeDigest, ...],
        login_method: LoginMethod,
        event: SecurityEvent,
        now: datetime,
    ) -> TOTPMethod | None:
        """Confirm a pending TOTP enrollment and replace the account's recovery codes in one transaction.

        Returns:
            Activated ``TOTPMethod``, or ``None`` if missing, expired, or already confirmed.
        """
        return await self._activate(
            account_id,
            enrollment_id,
            accepted_counter=accepted_counter,
            login_method=login_method,
            event=event,
            now=now,
            codes=codes,
        )

    async def get_totp_method(self, account_id: str, method_id: str) -> TOTPMethod | None:
        """Load an active TOTP method owned by the specified account.

        Returns:
            Confirmed ``TOTPMethod``, or ``None`` if not found.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return None
        async with MFAFactorService.new(config=self._alchemy_config) as mfa_factors:
            mfa_factor = await mfa_factors.find_active(user_id, method_id)
            return mfa_factors.to_totp_method(mfa_factor) if mfa_factor is not None else None

    async def advance_totp_counter(self, method_id: str, *, accepted_counter: int, now: datetime) -> bool:
        """Advance a TOTP method's counter only when strictly greater than the previous value.

        Returns:
            ``True`` if the counter advanced, ``False`` otherwise.
        """
        async with MFAFactorService.new(config=self._alchemy_config) as mfa_factors:
            advanced = await mfa_factors.advance_counter(method_id, accepted_counter=accepted_counter, now=now)
            await mfa_factors.repository.session.commit()
            return advanced

    async def replace_recovery_codes(
        self,
        account_id: str,
        codes: tuple[RecoveryCodeDigest, ...],
        *,
        now: datetime,
    ) -> None:
        """Replace all recovery code digests for an account in one transaction."""
        del now
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return
        async with MFAServices.new(config=self._alchemy_config) as services:
            await services.replace_recovery_codes(user_id, codes)
            await services.session.commit()

    async def consume_recovery_code(self, account_id: str, digest: bytes, *, now: datetime) -> bool:
        """Consume one matching unused recovery code digest.

        Returns:
            ``True`` if a matching unused recovery code was consumed, ``False`` otherwise.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return False
        async with MFARecoveryCodeService.new(config=self._alchemy_config) as recovery_codes:
            burned = await recovery_codes.burn(user_id, digest, now=now)
            await recovery_codes.repository.session.commit()
            return burned

    async def _activate(
        self,
        account_id: str,
        enrollment_id: str,
        *,
        accepted_counter: int,
        login_method: LoginMethod,
        event: SecurityEvent,
        now: datetime,
        codes: tuple[RecoveryCodeDigest, ...] | None,
    ) -> TOTPMethod | None:
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return None
        async with MFAServices.new(config=self._alchemy_config) as services:
            mfa_factor = await services.activate_totp(
                user_id,
                enrollment_id,
                accepted_counter=accepted_counter,
                login_method=login_method,
                codes=codes,
                now=now,
            )
            if mfa_factor is None:
                return None
            await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return services.mfa_factors.to_totp_method(mfa_factor)


class SQLAlchemyStepUpService:
    """Adapter implementing ``StepUpStore`` for single-use step-up authentication grants."""

    __slots__ = ("_alchemy_config",)

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the step-up grant store."""
        self._alchemy_config = alchemy_config

    async def put(self, record: StepUpGrantState) -> None:
        """Persist a short-lived step-up grant."""
        async with StepUpGrantService.new(config=self._alchemy_config) as step_up_grants:
            await step_up_grants.create(record, auto_commit=True)

    async def consume(
        self,
        grant_digest: bytes,
        *,
        principal_id: str,
        security_epoch: int,
        purpose: str,
        transport_digest: bytes,
        now: datetime,
    ) -> StepUpGrantState | None:
        """Spend a step-up grant matching every binding and expiry check.

        Returns:
            Consumed ``StepUpGrantState`` when valid, otherwise ``None``.
        """
        async with StepUpGrantService.new(config=self._alchemy_config) as step_up_grants:
            grant = await step_up_grants.redeem(
                grant_digest,
                principal_id=principal_id,
                security_epoch=security_epoch,
                purpose=purpose,
                transport_digest=transport_digest,
                now=now,
            )
            await step_up_grants.repository.session.commit()
        return grant


class SQLAlchemyMFALoginChallengeService:
    """Adapter implementing ``MFALoginChallengeStore`` with burn-on-consume and burn-on-mismatch."""

    __slots__ = ("_alchemy_config",)

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the MFA login challenge store."""
        self._alchemy_config = alchemy_config

    async def put(self, challenge: MFALoginChallenge) -> None:
        """Persist a single-use MFA login challenge, rejecting a non-UUID ``account_id`` with ``ValueError``."""
        async with MFALoginChallengeService.new(config=self._alchemy_config) as login_challenges:
            await login_challenges.create(challenge, auto_commit=True)

    async def consume(
        self,
        challenge_digest: bytes,
        *,
        account_id: str,
        security_epoch: int,
        now: datetime,
    ) -> MFALoginChallenge | None:
        """Burn the challenge and return it only if account, epoch, and expiry match.

        Returns:
            Consumed ``MFALoginChallenge`` when all checks pass, otherwise ``None``.
        """
        async with MFALoginChallengeService.new(config=self._alchemy_config) as login_challenges:
            challenge = await login_challenges.redeem(
                challenge_digest,
                account_id=account_id,
                security_epoch=security_epoch,
                now=now,
            )
            await login_challenges.repository.session.commit()
        return challenge
