"""SQLAlchemy persistence adapter for ``litestar-security`` WebAuthn passkeys and ceremony challenges."""

from __future__ import annotations

from datetime import UTC, datetime
from hmac import compare_digest
from typing import TYPE_CHECKING
from uuid import UUID

from anyio import Lock
from litestar_security.accounts import (
    LoginMethod,
    PasskeyAssertionStatus,
    PasskeyCredential,
    SecurityEvent,
    UserVerification,
    WebAuthnChallenge,
)
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.db import models as m
from app.domain.accounts.security.backend import persist_login_method

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

__all__ = ("SQLAlchemyPasskeyStore",)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_uuid(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def _row_to_credential(row: m.UserPasskey) -> PasskeyCredential:
    return PasskeyCredential(
        credential_id=bytes.fromhex(row.credential_id),
        account_id=str(row.user_id),
        public_key=row.public_key,
        sign_count=row.sign_count,
        backup_eligible=row.backup_eligible,
        backup_state=row.backup_state,
        user_verified=row.user_verified,
        aaguid=row.aaguid or "",
        attestation_format=row.attestation_format or "none",
        created_at=_ensure_utc(row.created_at),
        version=row.version,
        display_name=row.display_name,
        suspect=row.suspect,
        last_used_at=_ensure_utc(row.last_used_at) if row.last_used_at is not None else None,
        hardware_backed=row.hardware_backed,
    )


class SQLAlchemyPasskeyStore:
    """SQLAlchemy adapter implementing both ``PasskeyStore`` and ``WebAuthnChallengeStore``."""

    __slots__ = ("_alchemy_config", "_lock")

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the passkey and WebAuthn challenge store."""
        self._alchemy_config = alchemy_config
        self._lock = Lock()

    async def add_credential(
        self,
        credential: PasskeyCredential,
        *,
        login_method: LoginMethod,
        event: SecurityEvent,
    ) -> bool:
        """Persist a new WebAuthn passkey credential and its login method atomically.

        Returns:
            ``True`` if stored, ``False`` if ``account_id`` is invalid or the credential already exists.
        """
        del event
        uid = _parse_uuid(credential.account_id)
        if uid is None:
            return False
        created_at = _ensure_utc(credential.created_at)
        row = m.UserPasskey(
            credential_id=credential.credential_id.hex(),
            user_id=uid,
            public_key=credential.public_key,
            sign_count=credential.sign_count,
            backup_eligible=credential.backup_eligible,
            backup_state=credential.backup_state,
            user_verified=credential.user_verified,
            aaguid=credential.aaguid,
            attestation_format=credential.attestation_format,
            version=credential.version,
            display_name=credential.display_name,
            suspect=credential.suspect,
            hardware_backed=credential.hardware_backed,
            created_at=created_at,
            updated_at=created_at,
            last_used_at=_ensure_utc(credential.last_used_at) if credential.last_used_at is not None else None,
        )
        async with self._lock, self._alchemy_config.get_session() as session:
            session.add(row)
            try:
                await session.flush()
                await persist_login_method(session, credential.account_id, login_method)
                await session.commit()
            except IntegrityError:
                await session.rollback()
                return False
            return True

    async def get_credential(self, credential_id: bytes) -> PasskeyCredential | None:
        """Load one passkey credential by raw credential identifier bytes.

        Returns:
            Matching passkey credential, or ``None`` if not found.
        """
        async with self._alchemy_config.get_session() as session:
            row = await session.scalar(select(m.UserPasskey).where(m.UserPasskey.credential_id == credential_id.hex()))
            return _row_to_credential(row) if row is not None else None

    async def list_credentials(self, account_id: str) -> tuple[PasskeyCredential, ...]:
        """List all passkey credentials owned by an account.

        Returns:
            Tuple of passkey credentials registered to ``account_id``.
        """
        uid = _parse_uuid(account_id)
        if uid is None:
            return ()
        async with self._alchemy_config.get_session() as session:
            rows = (await session.scalars(select(m.UserPasskey).where(m.UserPasskey.user_id == uid))).all()
            return tuple(_row_to_credential(row) for row in rows)

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
        now_utc = _ensure_utc(now)
        cid_hex = credential_id.hex()
        async with self._lock, self._alchemy_config.get_session() as session:
            existing = await session.scalar(select(m.UserPasskey).where(m.UserPasskey.credential_id == cid_hex))
            if existing is None:
                return PasskeyAssertionStatus.CONFLICT
            next_sign_count = max(existing.sign_count, sign_count)
            result = await session.execute(
                update(m.UserPasskey)
                .where(
                    m.UserPasskey.id == existing.id,
                    m.UserPasskey.version == expected_version,
                )
                .values(
                    version=expected_version + 1,
                    sign_count=next_sign_count,
                    backup_eligible=backup_eligible,
                    backup_state=backup_state,
                    suspect=existing.suspect or clone_risk,
                    last_used_at=now_utc,
                )
            )
            await session.commit()
            if int(getattr(result, "rowcount", 0) or 0) != 1:
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
        uid = _parse_uuid(account_id)
        if uid is None:
            return None
        cid_hex = credential_id.hex()
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserPasskey).where(
                    m.UserPasskey.user_id == uid,
                    m.UserPasskey.credential_id == cid_hex,
                )
            )
            if row is None:
                return None
            row.display_name = display_name
            await session.commit()
            return _row_to_credential(row)

    async def put(self, challenge: WebAuthnChallenge) -> None:
        """Persist a single-use WebAuthn ceremony challenge."""
        row = m.PasskeyChallenge(
            challenge_id=challenge.challenge_digest.hex(),
            binding_digest=challenge.binding_digest.hex(),
            purpose=challenge.purpose,
            user_id=_parse_uuid(challenge.account_id),
            rp_id=challenge.rp_id,
            origins=list(challenge.origins),
            user_verification=challenge.user_verification.value,
            algorithms=list(challenge.algorithms),
            expires_at=_ensure_utc(challenge.expires_at),
        )
        async with self._lock, self._alchemy_config.get_session() as session:
            session.add(row)
            await session.commit()

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
        now_utc = _ensure_utc(now)
        digest_hex = challenge_digest.hex()
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.PasskeyChallenge).where(
                    m.PasskeyChallenge.challenge_id == digest_hex,
                    m.PasskeyChallenge.consumed_at.is_(None),
                )
            )
            if row is None:
                return None
            burn = await session.execute(
                update(m.PasskeyChallenge)
                .where(
                    m.PasskeyChallenge.id == row.id,
                    m.PasskeyChallenge.consumed_at.is_(None),
                )
                .values(consumed_at=now_utc)
            )
            await session.commit()
            if int(getattr(burn, "rowcount", 0) or 0) != 1:
                return None
            if (
                row.binding_digest is None
                or not compare_digest(bytes.fromhex(row.binding_digest), binding_digest)
                or row.purpose != purpose
                or _ensure_utc(row.expires_at) <= now_utc
            ):
                return None
            return WebAuthnChallenge(
                challenge_digest=bytes.fromhex(row.challenge_id),
                binding_digest=bytes.fromhex(row.binding_digest),
                purpose=row.purpose,
                account_id=str(row.user_id) if row.user_id is not None else None,
                rp_id=row.rp_id,
                origins=tuple(row.origins),
                user_verification=UserVerification(row.user_verification),
                algorithms=tuple(row.algorithms),
                expires_at=_ensure_utc(row.expires_at),
            )
