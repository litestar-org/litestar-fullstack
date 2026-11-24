"""Async SQLAlchemy security backend implementing ``litestar-security`` local accounts and session protocols."""

from __future__ import annotations

import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime
from hmac import compare_digest
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from anyio import Lock
from litestar_security.accounts import (
    CreateSessionCommand,
    LocalAccountState,
    LoginMethod,
    NotificationCommand,
    PasswordChangeOutcome,
    PasswordChangeStatus,
    PasswordCredentialState,
    PasswordResetOutcome,
    PasswordResetStatus,
    PurposeTokenDelivery,
    RegistrationCommand,
    RegistrationOutcome,
    RegistrationStatus,
    ResolvedUserAuthSession,
    RevokeLoginMethodOutcome,
    RevokeLoginMethodStatus,
    SecurityEvent,
    TokenIssue,
    TokenPurpose,
    UserAuthSession,
    VerificationOutcome,
    VerificationStatus,
)
from litestar_security.authentication import InvalidCredentials, VerificationUnavailable
from sqlalchemy import delete, select, true, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload, undefer_group

from app.db import models as m
from app.lib.constants import DEFAULT_ACCESS_ROLE

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

_LOGIN_METHODS_NAMESPACE = "login_methods"
_PERMANENT_STORE_EXPIRY = datetime(9999, 12, 31, tzinfo=UTC)

__all__ = ("SQLAlchemySecurityBackend", "persist_login_method")


async def persist_login_method(session: AsyncSession, account_id: str, method: LoginMethod) -> None:
    """Upsert a ``LoginMethod`` projection inside the caller's open SQLAlchemy transaction."""
    key = f"{account_id}:{method.method_id}"
    payload = json.dumps(
        {
            "method_id": method.method_id,
            "kind": method.kind,
            "created_at": _ensure_utc(method.created_at).isoformat(),
            "display_name": method.display_name,
        }
    ).encode("utf-8")
    existing = await session.scalar(
        select(m.AppStore).where(
            m.AppStore.namespace == _LOGIN_METHODS_NAMESPACE,
            m.AppStore.key == key,
        )
    )
    if existing is not None:
        existing.value = payload
    else:
        session.add(
            m.AppStore(
                namespace=_LOGIN_METHODS_NAMESPACE,
                key=key,
                value=payload,
                expires_at=_PERMANENT_STORE_EXPIRY,
            )
        )


def _passkey_method_id_from_hex(credential_hex: str) -> str:
    raw = bytes.fromhex(credential_hex)
    return "pk_" + urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _credential_hex_from_passkey_method_id(method_id: str) -> str | None:
    if not method_id.startswith("pk_"):
        return None
    encoded = method_id[3:]
    padded = encoded + "=" * ((4 - len(encoded) % 4) % 4)
    try:
        return urlsafe_b64decode(padded.encode("ascii")).hex()
    except (ValueError, UnicodeEncodeError):
        return None


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_uuid(raw: str) -> UUID | None:
    try:
        return UUID(raw)
    except ValueError:
        return None


def _user_load_options() -> list[Any]:
    return [
        selectinload(m.User.roles).options(joinedload(m.UserRole.role, innerjoin=True)),
        selectinload(m.User.teams).options(joinedload(m.TeamMember.team, innerjoin=True)),
        selectinload(m.User.mfa_factors),
    ]


def _to_account_state(user: m.User) -> LocalAccountState[m.User]:
    return LocalAccountState(
        account_id=str(user.id),
        normalized_identifier=user.email,
        display_name=user.name,
        active=user.is_active,
        verified=user.is_verified,
        security_epoch=user.security_epoch,
        user=user,
    )


def _to_session_record(row: m.UserSession) -> UserAuthSession:
    return UserAuthSession(
        session_id=row.session_id,
        binding_id=row.binding_id,
        binding_digest=bytes.fromhex(row.binding_digest),
        account_id=str(row.user_id),
        security_epoch=row.security_epoch,
        created_at=_ensure_utc(row.created_at),
        authenticated_at=_ensure_utc(row.authenticated_at),
        last_seen_at=_ensure_utc(row.last_seen_at),
        expires_at=_ensure_utc(row.expires_at),
        display_metadata=dict(row.display_metadata or {}),
    )


class SQLAlchemySecurityBackend:
    """Async SQLAlchemy backend for ``LocalAuth`` accounts, purpose tokens, login methods, and sessions."""

    __slots__ = ("_alchemy_config", "_clock", "_lock", "_notification_handler")

    def __init__(
        self,
        alchemy_config: SQLAlchemyAsyncConfig,
        *,
        clock: Callable[[], datetime] | None = None,
        notification_handler: Callable[[NotificationCommand], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize the backend with an Advanced Alchemy config and optional notification callback."""
        self._alchemy_config = alchemy_config
        self._clock = clock if clock is not None else (lambda: datetime.now(UTC))
        self._notification_handler = notification_handler
        self._lock = Lock()

    async def find_for_login(self, normalized_identifier: str) -> LocalAccountState[m.User] | None:
        """Locate an account by normalized email address with authorization relationships eager-loaded."""
        async with self._alchemy_config.get_session() as session:
            stmt = select(m.User).where(m.User.email == normalized_identifier).options(*_user_load_options())
            user = await session.scalar(stmt)
            return _to_account_state(user) if user is not None else None

    async def get_by_id(self, account_id: str) -> LocalAccountState[m.User] | None:
        """Load an account by UUID string with authorization relationships eager-loaded."""
        uid = _parse_uuid(account_id)
        if uid is None:
            return None
        async with self._alchemy_config.get_session() as session:
            stmt = select(m.User).where(m.User.id == uid).options(*_user_load_options())
            user = await session.scalar(stmt)
            return _to_account_state(user) if user is not None else None

    async def current_epoch(self, account_id: str) -> int | None:
        """Return the current security epoch for the given user account."""
        uid = _parse_uuid(account_id)
        if uid is None:
            return None
        async with self._alchemy_config.get_session() as session:
            return await session.scalar(select(m.User.security_epoch).where(m.User.id == uid))

    async def get_password_state(self, account_id: str) -> PasswordCredentialState | None:
        """Return the password credential snapshot, undeferring ``security_sensitive`` columns."""
        uid = _parse_uuid(account_id)
        if uid is None:
            return None
        async with self._alchemy_config.get_session() as session:
            stmt = select(m.User).where(m.User.id == uid).options(undefer_group("security_sensitive"))
            user = await session.scalar(stmt)
            if user is None or user.hashed_password is None:
                return None
            return PasswordCredentialState(
                password_hash=user.hashed_password,
                security_epoch=user.security_epoch,
                active=user.is_active,
                verified=user.is_verified,
            )

    async def compare_and_replace_password(
        self,
        account_id: str,
        expected_hash: str,
        password_hash: str,
        *,
        event: SecurityEvent,
    ) -> bool:
        """Atomically compare-and-swap a stored password hash."""
        del event
        uid = _parse_uuid(account_id)
        if uid is None:
            return False
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await session.execute(
                update(m.User)
                .where(m.User.id == uid, m.User.hashed_password == expected_hash)
                .values(hashed_password=password_hash)
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0) == 1

    async def replace_password_and_bump_epoch(
        self,
        account_id: str,
        password_hash: str,
        *,
        expected_epoch: int,
        event: SecurityEvent,
    ) -> PasswordChangeOutcome:
        """Atomically replace a user's password hash and advance ``security_epoch``."""
        del event
        uid = _parse_uuid(account_id)
        if uid is None:
            return PasswordChangeOutcome(PasswordChangeStatus.NOT_FOUND)
        async with self._lock, self._alchemy_config.get_session() as session:
            exists = await session.scalar(select(m.User.id).where(m.User.id == uid))
            if exists is None:
                return PasswordChangeOutcome(PasswordChangeStatus.NOT_FOUND)
            next_epoch = expected_epoch + 1
            result = await session.execute(
                update(m.User)
                .where(m.User.id == uid, m.User.security_epoch == expected_epoch)
                .values(hashed_password=password_hash, security_epoch=next_epoch)
            )
            await session.commit()
            if int(getattr(result, "rowcount", 0) or 0) != 1:
                return PasswordChangeOutcome(PasswordChangeStatus.CONFLICT)
            return PasswordChangeOutcome(PasswordChangeStatus.CHANGED, next_epoch)

    async def list_methods(self, account_id: str) -> tuple[LoginMethod, ...]:
        """List registered login methods for an account across AppStore, confirmed MFA factors, and passkeys."""
        prefix = f"{account_id}:"
        uid = _parse_uuid(account_id)
        async with self._alchemy_config.get_session() as session:
            stmt = select(m.AppStore).where(
                m.AppStore.namespace == _LOGIN_METHODS_NAMESPACE,
                m.AppStore.key.startswith(prefix),
            )
            rows = (await session.scalars(stmt)).all()
            methods_by_id: dict[str, LoginMethod] = {}
            for row in rows:
                data = json.loads(row.value.decode("utf-8"))
                methods_by_id[data["method_id"]] = LoginMethod(
                    method_id=data["method_id"],
                    kind=data["kind"],
                    created_at=_ensure_utc(datetime.fromisoformat(data["created_at"])),
                    display_name=data.get("display_name"),
                )
            if uid is not None:
                user_row = await session.scalar(
                    select(m.User).where(m.User.id == uid).options(undefer_group("security_sensitive"))
                )
                if (
                    user_row is not None
                    and user_row.hashed_password is not None
                    and not any(method.kind == "password" for method in methods_by_id.values())
                ):
                    methods_by_id["password"] = LoginMethod(
                        method_id="password",
                        kind="password",
                        created_at=_ensure_utc(user_row.created_at),
                    )
                mfa_rows = (
                    await session.scalars(
                        select(m.UserMFAFactor).where(
                            m.UserMFAFactor.user_id == uid,
                            m.UserMFAFactor.is_confirmed.is_(true()),
                        )
                    )
                ).all()
                for factor in mfa_rows:
                    if factor.method_id not in methods_by_id:
                        methods_by_id[factor.method_id] = LoginMethod(
                            method_id=factor.method_id,
                            kind=factor.kind,
                            created_at=_ensure_utc(factor.created_at),
                        )
                passkey_rows = (await session.scalars(select(m.UserPasskey).where(m.UserPasskey.user_id == uid))).all()
                for pk_row in passkey_rows:
                    pk_method_id = _passkey_method_id_from_hex(pk_row.credential_id)
                    if pk_method_id not in methods_by_id:
                        methods_by_id[pk_method_id] = LoginMethod(
                            method_id=pk_method_id,
                            kind="passkey",
                            created_at=_ensure_utc(pk_row.created_at),
                            display_name=pk_row.display_name,
                        )
            return tuple(methods_by_id.values())

    async def register_login_method(
        self,
        account_id: str,
        method: LoginMethod,
        *,
        event: SecurityEvent,
    ) -> None:
        """Persist a login method record for an account."""
        del event
        async with self._lock, self._alchemy_config.get_session() as session:
            await persist_login_method(session, account_id, method)
            await session.commit()

    async def revoke_login_method(
        self,
        account_id: str,
        method_id: str,
        *,
        require_remaining: bool = True,
        event: SecurityEvent,
    ) -> RevokeLoginMethodOutcome:
        """Revoke one login method and its underlying MFA/passkey row atomically."""
        del event
        prefix = f"{account_id}:"
        target_key = f"{account_id}:{method_id}"
        uid = _parse_uuid(account_id)
        cred_hex = _credential_hex_from_passkey_method_id(method_id)
        async with self._lock, self._alchemy_config.get_session() as session:
            rows = (
                await session.scalars(
                    select(m.AppStore).where(
                        m.AppStore.namespace == _LOGIN_METHODS_NAMESPACE,
                        m.AppStore.key.startswith(prefix),
                    )
                )
            ).all()
            existing_ids = {row.key.removeprefix(prefix) for row in rows}
            target_store = next((row for row in rows if row.key == target_key), None)

            mfa_target: m.UserMFAFactor | None = None
            passkey_target: m.UserPasskey | None = None
            if uid is not None:
                has_password_method = any(
                    json.loads(row.value.decode("utf-8")).get("kind") == "password" for row in rows
                )
                if not has_password_method:
                    user_row = await session.scalar(
                        select(m.User).where(m.User.id == uid).options(undefer_group("security_sensitive"))
                    )
                    if user_row is not None and user_row.hashed_password is not None:
                        existing_ids.add("password")
                mfa_rows = (
                    await session.scalars(
                        select(m.UserMFAFactor).where(
                            m.UserMFAFactor.user_id == uid,
                            m.UserMFAFactor.is_confirmed.is_(true()),
                        )
                    )
                ).all()
                for factor in mfa_rows:
                    existing_ids.add(factor.method_id)
                    if factor.method_id == method_id:
                        mfa_target = factor
                pk_rows = (await session.scalars(select(m.UserPasskey).where(m.UserPasskey.user_id == uid))).all()
                for pk_row in pk_rows:
                    pk_id = _passkey_method_id_from_hex(pk_row.credential_id)
                    existing_ids.add(pk_id)
                    if cred_hex is not None and pk_row.credential_id == cred_hex:
                        passkey_target = pk_row

            if target_store is None and mfa_target is None and passkey_target is None:
                return RevokeLoginMethodOutcome(RevokeLoginMethodStatus.NOT_FOUND)
            if require_remaining and len(existing_ids) <= 1:
                return RevokeLoginMethodOutcome(RevokeLoginMethodStatus.FINAL_METHOD)

            if target_store is not None:
                await session.execute(delete(m.AppStore).where(m.AppStore.id == target_store.id))
            if mfa_target is not None:
                await session.execute(delete(m.UserMFAFactor).where(m.UserMFAFactor.id == mfa_target.id))
            if passkey_target is not None:
                await session.execute(delete(m.UserPasskey).where(m.UserPasskey.id == passkey_target.id))
            await session.commit()
            return RevokeLoginMethodOutcome(RevokeLoginMethodStatus.REVOKED)

    async def register(
        self,
        command: RegistrationCommand,
        password_hash: str,
        *,
        invitation_digest: bytes | None,
        verification: PurposeTokenDelivery | None,
        now: datetime,
        event: SecurityEvent,
    ) -> RegistrationOutcome[m.User]:
        """Atomically register a new user, assign the default role, and persist optional verification token."""
        del event
        notification: NotificationCommand | None = None
        async with self._lock, self._alchemy_config.get_session() as session:
            existing = await session.scalar(select(m.User.id).where(m.User.email == command.normalized_identifier))
            if existing is not None:
                return RegistrationOutcome(RegistrationStatus.DUPLICATE)

            invitation_row: m.PurposeToken | None = None
            if invitation_digest is not None:
                invitation_row = await session.scalar(
                    select(m.PurposeToken).where(
                        m.PurposeToken.purpose == TokenPurpose.INVITATION.value,
                        m.PurposeToken.token_hash == invitation_digest.hex(),
                        m.PurposeToken.consumed_at.is_(None),
                        m.PurposeToken.revoked_at.is_(None),
                    )
                )
                if invitation_row is None or _ensure_utc(invitation_row.expires_at) <= now:
                    return RegistrationOutcome(RegistrationStatus.INVALID_INVITATION)

            if verification is not None:
                existing_token = await session.scalar(
                    select(m.PurposeToken.id).where(m.PurposeToken.token_id == verification.issue.token_id)
                )
                if existing_token is not None:
                    msg = "Purpose token identifier collision"
                    raise ValueError(msg)

            user = m.User(
                email=command.normalized_identifier,
                name=command.display_name,
                hashed_password=password_hash,
                is_active=True,
                is_verified=verification is None,
                verified_at=now.date() if verification is None else None,
                security_epoch=1,
            )
            session.add(user)
            try:
                await session.flush()
            except IntegrityError:
                await session.rollback()
                return RegistrationOutcome(RegistrationStatus.DUPLICATE)

            default_role = await session.scalar(select(m.Role).where(m.Role.name == DEFAULT_ACCESS_ROLE))
            if default_role is not None:
                session.add(m.UserRole(user_id=user.id, role_id=default_role.id, assigned_at=now))

            if verification is not None:
                issue, notification = verification.bind(str(user.id))
                session.add(
                    m.PurposeToken(
                        token_id=issue.token_id,
                        token_hash=issue.digest.hex(),
                        purpose=issue.purpose.value,
                        user_id=user.id,
                        account_ref=issue.account_id,
                        issued_security_epoch=issue.issued_security_epoch,
                        attempts=0,
                        maximum_attempts=issue.maximum_attempts,
                        expires_at=_ensure_utc(issue.expires_at),
                    )
                )

            if invitation_row is not None:
                invitation_row.consumed_at = now

            await session.commit()

            loaded = await session.scalar(select(m.User).where(m.User.id == user.id).options(*_user_load_options()))
            account_state = _to_account_state(loaded if loaded is not None else user)

        if notification is not None and self._notification_handler is not None:
            await self._notification_handler(notification)
        return RegistrationOutcome(RegistrationStatus.CREATED, account_state)

    async def issue(
        self,
        issue: TokenIssue,
        notification: NotificationCommand,
        *,
        event: SecurityEvent,
    ) -> None:
        """Persist a single-use purpose token digest and dispatch its notification callback."""
        del event
        async with self._lock, self._alchemy_config.get_session() as session:
            existing = await session.scalar(select(m.PurposeToken.id).where(m.PurposeToken.token_id == issue.token_id))
            if existing is not None:
                msg = "Purpose token identifier collision"
                raise ValueError(msg)
            session.add(
                m.PurposeToken(
                    token_id=issue.token_id,
                    token_hash=issue.digest.hex(),
                    purpose=issue.purpose.value,
                    user_id=_parse_uuid(issue.account_id),
                    account_ref=issue.account_id,
                    issued_security_epoch=issue.issued_security_epoch,
                    attempts=0,
                    maximum_attempts=issue.maximum_attempts,
                    expires_at=_ensure_utc(issue.expires_at),
                )
            )
            await session.commit()
        if self._notification_handler is not None:
            await self._notification_handler(notification)

    async def issue_absent(self) -> None:
        """Perform a constant-interface no-op when issuing for a non-existent account."""
        return

    async def _consume_purpose_token(
        self,
        session: Any,
        *,
        token_id: str,
        digest: bytes,
        purpose: TokenPurpose,
        now: datetime,
    ) -> m.User | str:
        token = await session.scalar(select(m.PurposeToken).where(m.PurposeToken.token_id == token_id))
        if token is None or token.purpose != purpose.value:
            return "invalid"
        if token.consumed_at is not None or token.revoked_at is not None:
            return "used"
        if not compare_digest(bytes.fromhex(token.token_hash), digest):
            token.attempts += 1
            if token.attempts >= token.maximum_attempts:
                token.consumed_at = now
            await session.commit()
            return "invalid"
        if _ensure_utc(token.expires_at) <= now:
            return "expired"

        user = (
            await session.scalar(select(m.User).where(m.User.id == token.user_id))
            if token.user_id is not None
            else None
        )
        if user is None or (purpose is TokenPurpose.RECOVERY and user.security_epoch != token.issued_security_epoch):
            return "conflict"

        burn = await session.execute(
            update(m.PurposeToken)
            .where(m.PurposeToken.id == token.id, m.PurposeToken.consumed_at.is_(None))
            .values(consumed_at=now)
        )
        burned = int(getattr(burn, "rowcount", 0) or 0) == 1
        if not burned:
            await session.rollback()
        return user if burned else "used"

    async def consume_and_verify(
        self,
        token_id: str,
        digest: bytes,
        *,
        now: datetime,
        event: SecurityEvent,
    ) -> VerificationOutcome:
        """Atomically consume a verification token and mark the owning account verified."""
        del event
        status_map = {
            "invalid": VerificationStatus.INVALID,
            "used": VerificationStatus.USED,
            "expired": VerificationStatus.EXPIRED,
            "conflict": VerificationStatus.INVALID,
        }
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await self._consume_purpose_token(
                session,
                token_id=token_id,
                digest=digest,
                purpose=TokenPurpose.VERIFICATION,
                now=now,
            )
            if isinstance(result, str):
                return VerificationOutcome(status_map[result])
            result.is_verified = True
            result.verified_at = now.date()
            await session.commit()
            return VerificationOutcome(VerificationStatus.CONSUMED, str(result.id), result.security_epoch)

    async def consume_and_reset(
        self,
        token_id: str,
        digest: bytes,
        new_password_hash: str,
        *,
        now: datetime,
        event: SecurityEvent,
    ) -> PasswordResetOutcome:
        """Atomically consume a recovery token, replace the password hash, and bump ``security_epoch``."""
        del event
        status_map = {
            "invalid": PasswordResetStatus.INVALID,
            "used": PasswordResetStatus.USED,
            "expired": PasswordResetStatus.EXPIRED,
            "conflict": PasswordResetStatus.CONFLICT,
        }
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await self._consume_purpose_token(
                session,
                token_id=token_id,
                digest=digest,
                purpose=TokenPurpose.RECOVERY,
                now=now,
            )
            if isinstance(result, str):
                return PasswordResetOutcome(status_map[result])
            next_epoch = result.security_epoch + 1
            result.hashed_password = new_password_hash
            result.security_epoch = next_epoch
            result.password_reset_at = now
            await session.commit()
            return PasswordResetOutcome(PasswordResetStatus.RESET, str(result.id), next_epoch)

    async def create(
        self,
        command: CreateSessionCommand,
        *,
        event: SecurityEvent,
    ) -> UserAuthSession:
        """Persist a new authenticated browser session."""
        del event
        uid = _parse_uuid(command.account_id)
        if uid is None:
            msg = "Session account_id must be a valid UUID"
            raise ValueError(msg)
        created_at = _ensure_utc(command.created_at)
        row = m.UserSession(
            session_id=command.session_id,
            binding_id=command.binding_id,
            binding_digest=command.binding_digest.hex(),
            user_id=uid,
            security_epoch=command.security_epoch,
            created_at=created_at,
            updated_at=created_at,
            authenticated_at=_ensure_utc(command.authenticated_at),
            last_seen_at=created_at,
            expires_at=_ensure_utc(command.expires_at),
            display_metadata=dict(command.display_metadata),
        )
        async with self._lock, self._alchemy_config.get_session() as session:
            session.add(row)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                msg = "Session identifier collision"
                raise ValueError(msg) from exc
            return _to_session_record(row)

    async def get(self, session_id: str) -> UserAuthSession | None:
        """Return an active, unexpired session record or ``None``."""
        now = _ensure_utc(self._clock())
        async with self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserSession).where(
                    m.UserSession.session_id == session_id,
                    m.UserSession.revoked_at.is_(None),
                )
            )
            if row is None or _ensure_utc(row.expires_at) <= now:
                return None
            return _to_session_record(row)

    async def list_for_account(self, account_id: str) -> tuple[UserAuthSession, ...]:
        """List active, unexpired sessions for one user account."""
        uid = _parse_uuid(account_id)
        if uid is None:
            return ()
        now = _ensure_utc(self._clock())
        async with self._alchemy_config.get_session() as session:
            rows = (
                await session.scalars(
                    select(m.UserSession).where(
                        m.UserSession.user_id == uid,
                        m.UserSession.revoked_at.is_(None),
                    )
                )
            ).all()
            return tuple(_to_session_record(row) for row in rows if _ensure_utc(row.expires_at) > now)

    async def touch(self, session_id: str, *, now: datetime) -> UserAuthSession | None:
        """Advance ``last_seen_at`` on an active, unexpired session."""
        current = _ensure_utc(self._clock())
        touch_at = _ensure_utc(now)
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserSession).where(
                    m.UserSession.session_id == session_id,
                    m.UserSession.revoked_at.is_(None),
                )
            )
            if row is None:
                return None
            expires_at = _ensure_utc(row.expires_at)
            if expires_at <= touch_at or expires_at <= current:
                return None
            row.last_seen_at = touch_at
            await session.commit()
            return _to_session_record(row)

    async def revoke_session_for_account(
        self,
        account_id: str,
        session_id: str,
        *,
        event: SecurityEvent,
    ) -> bool:
        """Revoke one session owned by the given account."""
        del event
        uid = _parse_uuid(account_id)
        if uid is None:
            return False
        now = _ensure_utc(self._clock())
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await session.execute(
                update(m.UserSession)
                .where(
                    m.UserSession.session_id == session_id,
                    m.UserSession.user_id == uid,
                    m.UserSession.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0) == 1

    async def revoke_sessions_for_account(
        self,
        account_id: str,
        *,
        event: SecurityEvent,
    ) -> int:
        """Revoke all active sessions owned by the given account."""
        del event
        uid = _parse_uuid(account_id)
        if uid is None:
            return 0
        now = _ensure_utc(self._clock())
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await session.execute(
                update(m.UserSession)
                .where(
                    m.UserSession.user_id == uid,
                    m.UserSession.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0)

    async def revoke_other_sessions(
        self,
        account_id: str,
        session_id: str,
        *,
        event: SecurityEvent,
    ) -> int:
        """Revoke all active sessions for an account except the specified current session."""
        del event
        uid = _parse_uuid(account_id)
        if uid is None:
            return 0
        now = _ensure_utc(self._clock())
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await session.execute(
                update(m.UserSession)
                .where(
                    m.UserSession.user_id == uid,
                    m.UserSession.session_id != session_id,
                    m.UserSession.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0)

    async def rebind(
        self,
        prior_session_id: str,
        command: CreateSessionCommand,
        *,
        event: SecurityEvent,
    ) -> UserAuthSession | None:
        """Atomically replace a prior active session with a successor session."""
        del event
        uid = _parse_uuid(command.account_id)
        if uid is None:
            return None
        now = _ensure_utc(self._clock())
        created_at = _ensure_utc(command.created_at)
        async with self._lock, self._alchemy_config.get_session() as session:
            revoked = await session.execute(
                update(m.UserSession)
                .where(
                    m.UserSession.session_id == prior_session_id,
                    m.UserSession.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            if int(getattr(revoked, "rowcount", 0) or 0) != 1:
                await session.rollback()
                return None

            replacement = m.UserSession(
                session_id=command.session_id,
                binding_id=command.binding_id,
                binding_digest=command.binding_digest.hex(),
                user_id=uid,
                security_epoch=command.security_epoch,
                created_at=created_at,
                updated_at=created_at,
                authenticated_at=_ensure_utc(command.authenticated_at),
                last_seen_at=created_at,
                expires_at=_ensure_utc(command.expires_at),
                display_metadata=dict(command.display_metadata),
            )
            session.add(replacement)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                msg = "Session identifier collision"
                raise ValueError(msg) from exc
            return _to_session_record(replacement)

    async def resolve_user_auth_session(
        self,
        session_id: str,
        account_id: str,
        *,
        now: datetime,
    ) -> ResolvedUserAuthSession[m.User] | None:
        """Resolve an active session and eager-loaded user in one session scope.

        Database errors propagate to ``NativeSessionAuth.authenticate`` which
        fails closed with ``VerificationUnavailable``.
        """
        uid = _parse_uuid(account_id)
        if uid is None:
            return None
        check_at = _ensure_utc(now)
        async with self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserSession).where(
                    m.UserSession.session_id == session_id,
                    m.UserSession.user_id == uid,
                    m.UserSession.revoked_at.is_(None),
                )
            )
            if row is None or _ensure_utc(row.expires_at) <= check_at:
                return None
            user = await session.scalar(select(m.User).where(m.User.id == uid).options(*_user_load_options()))
            if user is None:
                return None
            return ResolvedUserAuthSession(
                session=_to_session_record(row),
                account=_to_account_state(user),
            )

    async def resolve_session(
        self,
        session_id: str,
        account_id: str,
        *,
        now: datetime | None = None,
    ) -> ResolvedUserAuthSession[m.User] | InvalidCredentials | VerificationUnavailable:
        """Fail-closed session lookup converting storage errors to ``VerificationUnavailable``."""
        try:
            resolved = await self.resolve_user_auth_session(
                session_id,
                account_id,
                now=now if now is not None else self._clock(),
            )
        except SQLAlchemyError:
            logger.warning("Database error during session resolution", session_id=session_id)
            return VerificationUnavailable()
        if resolved is None:
            return InvalidCredentials()
        return resolved
