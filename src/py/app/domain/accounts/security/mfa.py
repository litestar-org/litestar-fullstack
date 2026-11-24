"""SQLAlchemy persistence adapters for ``litestar-security`` MFA, step-up grants, and login challenges."""

from __future__ import annotations

from datetime import UTC, datetime
from hmac import compare_digest
from typing import TYPE_CHECKING, Literal, cast
from uuid import UUID

from anyio import Lock
from litestar_security.accounts import (
    AESGCMSecretProtector,
    LoginMethod,
    MFALoginChallenge,
    PendingTOTPEnrollment,
    ProtectedSecret,
    RecoveryCodeDigest,
    SecretProtectorKey,
    SecurityEvent,
    StepUpGrantState,
    TOTPMethod,
    TOTPPolicy,
)
from sqlalchemy import delete, or_, select, update

from app.db import models as m
from app.domain.accounts.security.backend import persist_login_method
from app.lib.secrets import TOTP_PROTECTOR_INFO, derive_subkey

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

    from app.lib.settings import Settings

__all__ = (
    "SQLAlchemyMFALoginChallengeService",
    "SQLAlchemyMFAService",
    "SQLAlchemyStepUpService",
    "build_secret_protector",
)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_uuid(raw: str) -> UUID | None:
    try:
        return UUID(raw)
    except ValueError:
        return None


def build_secret_protector(
    settings: Settings,
    *,
    key_version: str = "v1",
    retained_keys: Sequence[SecretProtectorKey] = (),
) -> AESGCMSecretProtector:
    """Build an ``AESGCMSecretProtector`` backed by an HKDF-derived 32-byte key."""
    active = SecretProtectorKey(
        key_version=key_version,
        key=derive_subkey(settings.app.SECRET_KEY, TOTP_PROTECTOR_INFO),
    )
    return AESGCMSecretProtector(active_key=active, retained_keys=tuple(retained_keys))


_TOTP_LONG_DIGITS = 8


def _row_to_totp_policy(row: m.UserMFAFactor) -> TOTPPolicy:
    digits: Literal[6, 8] = 8 if row.digits == _TOTP_LONG_DIGITS else 6
    algorithm = cast("Literal['SHA1', 'SHA256', 'SHA512']", row.algorithm)
    return TOTPPolicy(
        digits=digits,
        period_seconds=row.period_seconds,
        algorithm=algorithm,
        allowed_drift_steps=row.allowed_drift_steps,
    )


def _row_to_totp_method(row: m.UserMFAFactor) -> TOTPMethod:
    return TOTPMethod(
        method_id=row.method_id,
        account_id=str(row.user_id),
        protected_secret=ProtectedSecret(ciphertext=row.secret_ciphertext, key_version=row.key_version),
        policy=_row_to_totp_policy(row),
        last_accepted_counter=row.last_accepted_counter if row.last_accepted_counter is not None else -1,
        created_at=_ensure_utc(row.created_at),
        last_used_at=_ensure_utc(row.last_used_at) if row.last_used_at is not None else None,
    )


class SQLAlchemyMFAService:
    """SQLAlchemy ``MFAStore`` persisting encrypted TOTP factors and peppered recovery code digests."""

    __slots__ = ("_alchemy_config", "_lock")

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the MFA store."""
        self._alchemy_config = alchemy_config
        self._lock = Lock()

    async def create_totp_enrollment(self, enrollment: PendingTOTPEnrollment) -> None:
        """Persist a pending encrypted TOTP enrollment."""
        uid = _parse_uuid(enrollment.account_id)
        if uid is None:
            msg = "TOTP enrollment account_id must be a valid UUID"
            raise ValueError(msg)
        row = m.UserMFAFactor(
            method_id=enrollment.method_id,
            enrollment_id=enrollment.enrollment_id,
            user_id=uid,
            kind="totp",
            secret_ciphertext=enrollment.protected_secret.ciphertext,
            key_version=enrollment.protected_secret.key_version,
            digits=enrollment.policy.digits,
            period_seconds=enrollment.policy.period_seconds,
            algorithm=enrollment.policy.algorithm,
            allowed_drift_steps=enrollment.policy.allowed_drift_steps,
            is_confirmed=False,
            created_at=_ensure_utc(enrollment.created_at),
            updated_at=_ensure_utc(enrollment.created_at),
            expires_at=_ensure_utc(enrollment.expires_at),
        )
        async with self._lock, self._alchemy_config.get_session() as session:
            session.add(row)
            await session.commit()

    async def get_totp_enrollment(self, enrollment_id: str) -> PendingTOTPEnrollment | None:
        """Load a pending TOTP enrollment by identifier."""
        async with self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserMFAFactor).where(
                    m.UserMFAFactor.enrollment_id == enrollment_id,
                    m.UserMFAFactor.is_confirmed.is_(False),
                )
            )
            if row is None or row.enrollment_id is None or row.expires_at is None:
                return None
            return PendingTOTPEnrollment(
                enrollment_id=row.enrollment_id,
                method_id=row.method_id,
                account_id=str(row.user_id),
                protected_secret=ProtectedSecret(ciphertext=row.secret_ciphertext, key_version=row.key_version),
                policy=_row_to_totp_policy(row),
                created_at=_ensure_utc(row.created_at),
                expires_at=_ensure_utc(row.expires_at),
            )

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
        """Atomically confirm a pending TOTP enrollment and register its login method."""
        del event
        return await self._activate(
            account_id,
            enrollment_id,
            accepted_counter=accepted_counter,
            login_method=login_method,
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
        """Atomically confirm a pending TOTP enrollment, register its login method, and replace recovery codes."""
        del event
        return await self._activate(
            account_id,
            enrollment_id,
            accepted_counter=accepted_counter,
            login_method=login_method,
            now=now,
            codes=codes,
        )

    async def _activate(
        self,
        account_id: str,
        enrollment_id: str,
        *,
        accepted_counter: int,
        login_method: LoginMethod,
        now: datetime,
        codes: tuple[RecoveryCodeDigest, ...] | None,
    ) -> TOTPMethod | None:
        uid = _parse_uuid(account_id)
        if uid is None:
            return None
        now_utc = _ensure_utc(now)
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserMFAFactor).where(
                    m.UserMFAFactor.enrollment_id == enrollment_id,
                    m.UserMFAFactor.user_id == uid,
                    m.UserMFAFactor.is_confirmed.is_(False),
                )
            )
            if row is None:
                return None
            if row.expires_at is not None and _ensure_utc(row.expires_at) <= now_utc:
                return None
            result = await session.execute(
                update(m.UserMFAFactor)
                .where(
                    m.UserMFAFactor.id == row.id,
                    m.UserMFAFactor.is_confirmed.is_(False),
                )
                .values(
                    is_confirmed=True,
                    enrollment_id=None,
                    expires_at=None,
                    last_accepted_counter=accepted_counter,
                    last_used_at=now_utc,
                )
            )
            if int(getattr(result, "rowcount", 0) or 0) != 1:
                await session.rollback()
                return None
            await persist_login_method(session, account_id, login_method)
            if codes is not None:
                await session.execute(delete(m.UserMFARecoveryCode).where(m.UserMFARecoveryCode.user_id == uid))
                for code in codes:
                    if code.account_id == account_id:
                        session.add(
                            m.UserMFARecoveryCode(
                                user_id=uid,
                                pepper_version=code.pepper_version,
                                digest=code.digest.hex(),
                            )
                        )
            await session.commit()
            refreshed = await session.scalar(select(m.UserMFAFactor).where(m.UserMFAFactor.id == row.id))
            return _row_to_totp_method(refreshed) if refreshed is not None else None

    async def get_totp_method(self, account_id: str, method_id: str) -> TOTPMethod | None:
        """Load an active TOTP method owned by the specified account."""
        uid = _parse_uuid(account_id)
        if uid is None:
            return None
        async with self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserMFAFactor).where(
                    m.UserMFAFactor.user_id == uid,
                    m.UserMFAFactor.method_id == method_id,
                    m.UserMFAFactor.is_confirmed.is_(True),
                )
            )
            return _row_to_totp_method(row) if row is not None else None

    async def advance_totp_counter(self, method_id: str, *, accepted_counter: int, now: datetime) -> bool:
        """Atomically advance a TOTP method's counter only when strictly greater than the previous value."""
        now_utc = _ensure_utc(now)
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await session.execute(
                update(m.UserMFAFactor)
                .where(
                    m.UserMFAFactor.method_id == method_id,
                    m.UserMFAFactor.is_confirmed.is_(True),
                    or_(
                        m.UserMFAFactor.last_accepted_counter.is_(None),
                        m.UserMFAFactor.last_accepted_counter < accepted_counter,
                    ),
                )
                .values(last_accepted_counter=accepted_counter, last_used_at=now_utc)
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0) == 1

    async def replace_recovery_codes(
        self,
        account_id: str,
        codes: tuple[RecoveryCodeDigest, ...],
        *,
        now: datetime,
    ) -> None:
        """Atomically replace all recovery code digests for an account."""
        del now
        uid = _parse_uuid(account_id)
        if uid is None:
            return
        async with self._lock, self._alchemy_config.get_session() as session:
            await session.execute(delete(m.UserMFARecoveryCode).where(m.UserMFARecoveryCode.user_id == uid))
            for code in codes:
                if code.account_id == account_id:
                    session.add(
                        m.UserMFARecoveryCode(
                            user_id=uid,
                            pepper_version=code.pepper_version,
                            digest=code.digest.hex(),
                        )
                    )
            await session.commit()

    async def consume_recovery_code(self, account_id: str, digest: bytes, *, now: datetime) -> bool:
        """Atomically consume one matching unused recovery code digest."""
        uid = _parse_uuid(account_id)
        if uid is None:
            return False
        now_utc = _ensure_utc(now)
        digest_hex = digest.hex()
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await session.execute(
                update(m.UserMFARecoveryCode)
                .where(
                    m.UserMFARecoveryCode.user_id == uid,
                    m.UserMFARecoveryCode.digest == digest_hex,
                    m.UserMFARecoveryCode.consumed_at.is_(None),
                )
                .values(consumed_at=now_utc)
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0) == 1


class SQLAlchemyStepUpService:
    """SQLAlchemy ``StepUpStore`` persisting single-use step-up authentication grants."""

    __slots__ = ("_alchemy_config", "_lock")

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the step-up grant store."""
        self._alchemy_config = alchemy_config
        self._lock = Lock()

    async def put(self, record: StepUpGrantState) -> None:
        """Persist a short-lived step-up grant."""
        row = m.StepUpGrant(
            grant_digest=record.grant_digest.hex(),
            transport_digest=record.transport_digest.hex(),
            principal_id=record.principal_id,
            security_epoch=record.security_epoch,
            purpose=record.purpose,
            methods=sorted(record.methods),
            traits=sorted(record.traits),
            authenticated_at=_ensure_utc(record.authenticated_at),
            expires_at=_ensure_utc(record.expires_at),
        )
        async with self._lock, self._alchemy_config.get_session() as session:
            session.add(row)
            await session.commit()

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
        """Atomically consume a step-up grant matching every binding and expiry check."""
        now_utc = _ensure_utc(now)
        digest_hex = grant_digest.hex()
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.StepUpGrant).where(
                    m.StepUpGrant.grant_digest == digest_hex,
                    m.StepUpGrant.revoked_at.is_(None),
                )
            )
            if row is None:
                return None
            if (
                row.principal_id != principal_id
                or row.security_epoch != security_epoch
                or row.purpose != purpose
                or not compare_digest(bytes.fromhex(row.transport_digest), transport_digest)
                or _ensure_utc(row.expires_at) <= now_utc
            ):
                return None
            result = await session.execute(
                update(m.StepUpGrant)
                .where(m.StepUpGrant.id == row.id, m.StepUpGrant.revoked_at.is_(None))
                .values(revoked_at=now_utc)
            )
            await session.commit()
            if int(getattr(result, "rowcount", 0) or 0) != 1:
                return None
            return StepUpGrantState(
                grant_digest=bytes.fromhex(row.grant_digest),
                transport_digest=bytes.fromhex(row.transport_digest),
                principal_id=row.principal_id,
                security_epoch=row.security_epoch,
                purpose=row.purpose,
                methods=frozenset(row.methods),
                traits=frozenset(row.traits),
                authenticated_at=_ensure_utc(row.authenticated_at),
                expires_at=_ensure_utc(row.expires_at),
            )


class SQLAlchemyMFALoginChallengeService:
    """SQLAlchemy ``MFALoginChallengeStore`` with atomic burn-on-consume and burn-on-mismatch."""

    __slots__ = ("_alchemy_config", "_lock")

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the MFA login challenge store."""
        self._alchemy_config = alchemy_config
        self._lock = Lock()

    async def put(self, challenge: MFALoginChallenge) -> None:
        """Persist a single-use MFA login challenge."""
        uid = _parse_uuid(challenge.account_id)
        if uid is None:
            msg = "MFA login challenge account_id must be a valid UUID"
            raise ValueError(msg)
        row = m.MFALoginChallenge(
            challenge_hash=challenge.challenge_digest.hex(),
            user_id=uid,
            security_epoch=challenge.security_epoch,
            client_key=challenge.client_key,
            issued_at=_ensure_utc(challenge.issued_at),
            expires_at=_ensure_utc(challenge.expires_at),
        )
        async with self._lock, self._alchemy_config.get_session() as session:
            session.add(row)
            await session.commit()

    async def consume(
        self,
        challenge_digest: bytes,
        *,
        account_id: str,
        security_epoch: int,
        now: datetime,
    ) -> MFALoginChallenge | None:
        """Atomically burn the challenge and return it only if account, epoch, and expiry match."""
        now_utc = _ensure_utc(now)
        digest_hex = challenge_digest.hex()
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.MFALoginChallenge).where(
                    m.MFALoginChallenge.challenge_hash == digest_hex,
                    m.MFALoginChallenge.consumed_at.is_(None),
                )
            )
            if row is None:
                return None
            burn = await session.execute(
                update(m.MFALoginChallenge)
                .where(
                    m.MFALoginChallenge.id == row.id,
                    m.MFALoginChallenge.consumed_at.is_(None),
                )
                .values(consumed_at=now_utc)
            )
            await session.commit()
            if int(getattr(burn, "rowcount", 0) or 0) != 1:
                return None
            if (
                str(row.user_id) != account_id
                or row.security_epoch != security_epoch
                or _ensure_utc(row.expires_at) <= now_utc
            ):
                return None
            return MFALoginChallenge(
                challenge_digest=bytes.fromhex(row.challenge_hash),
                account_id=str(row.user_id),
                security_epoch=row.security_epoch,
                client_key=row.client_key,
                issued_at=_ensure_utc(row.issued_at),
                expires_at=_ensure_utc(row.expires_at),
            )
