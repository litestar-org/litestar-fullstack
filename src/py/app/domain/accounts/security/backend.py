"""Persistence adapter for ``litestar-security`` local accounts, purpose tokens, login methods, and sessions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from advanced_alchemy.exceptions import RepositoryError
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
from sqlalchemy.exc import SQLAlchemyError

from app.db import models as m
from app.domain.accounts.security.events import security_audit_record
from app.domain.accounts.services import AccountSecurityServices, TokenRejection, UserService, UserSessionService

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from sqlalchemy import ColumnElement

logger = structlog.get_logger(__name__)

_VERIFICATION_REJECTIONS: dict[TokenRejection, VerificationStatus] = {
    "invalid": VerificationStatus.INVALID,
    "used": VerificationStatus.USED,
    "expired": VerificationStatus.EXPIRED,
    "conflict": VerificationStatus.INVALID,
}
_PASSWORD_RESET_REJECTIONS: dict[TokenRejection, PasswordResetStatus] = {
    "invalid": PasswordResetStatus.INVALID,
    "used": PasswordResetStatus.USED,
    "expired": PasswordResetStatus.EXPIRED,
    "conflict": PasswordResetStatus.CONFLICT,
}

__all__ = ("SQLAlchemySecurityBackend",)


class SQLAlchemySecurityBackend:
    """Adapter implementing the ``LocalAuth`` account, token, login method, and session ports on services."""

    __slots__ = ("_alchemy_config", "_clock", "_notification_handler")

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

    async def find_for_login(self, normalized_identifier: str) -> LocalAccountState[m.User] | None:
        """Locate an account by normalized email address with authorization relationships eager-loaded.

        Returns:
            Matching ``LocalAccountState``, or ``None`` if not found.
        """
        return await self._find_account(m.User.email == normalized_identifier)

    async def get_by_id(self, account_id: str) -> LocalAccountState[m.User] | None:
        """Load an account by UUID string with authorization relationships eager-loaded.

        Returns:
            Matching ``LocalAccountState``, or ``None`` if not found or invalid UUID.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return None
        return await self._find_account(m.User.id == user_id)

    async def current_epoch(self, account_id: str) -> int | None:
        """Return the current security epoch for the given user account."""
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return None
        async with UserService.new(config=self._alchemy_config) as users:
            return await users.get_security_epoch(user_id)

    async def get_password_state(self, account_id: str) -> PasswordCredentialState | None:
        """Return the password credential snapshot, undeferring ``security_sensitive`` columns."""
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return None
        async with UserService.new(config=self._alchemy_config) as users:
            user = await users.find_with_password(user_id)
            return users.to_password_state(user) if user is not None else None

    async def compare_and_replace_password(
        self,
        account_id: str,
        expected_hash: str,
        password_hash: str,
        *,
        event: SecurityEvent,
    ) -> bool:
        """Atomically compare-and-swap a stored password hash and record its audit event.

        Returns:
            ``True`` if the password hash was updated, ``False`` otherwise.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return False
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            swapped = await services.users.swap_password_hash(
                user_id,
                expected_hash=expected_hash,
                password_hash=password_hash,
            )
            if swapped:
                await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return swapped

    async def replace_password_and_bump_epoch(
        self,
        account_id: str,
        password_hash: str,
        *,
        expected_epoch: int,
        event: SecurityEvent,
    ) -> PasswordChangeOutcome:
        """Atomically replace a password hash, advance ``security_epoch``, and record the audit event.

        Returns:
            ``PasswordChangeOutcome`` indicating ``CHANGED``, ``CONFLICT``, or ``NOT_FOUND``.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return PasswordChangeOutcome(PasswordChangeStatus.NOT_FOUND)
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            if await services.users.replace_password_hash_and_bump_epoch(
                user_id,
                password_hash,
                expected_epoch=expected_epoch,
            ):
                await services.audit_logs.create(security_audit_record(event), auto_commit=True)
                return PasswordChangeOutcome(PasswordChangeStatus.CHANGED, expected_epoch + 1)
            if await services.users.exists(id=user_id):
                return PasswordChangeOutcome(PasswordChangeStatus.CONFLICT)
            return PasswordChangeOutcome(PasswordChangeStatus.NOT_FOUND)

    async def list_methods(self, account_id: str) -> tuple[LoginMethod, ...]:
        """List an account's login methods: recorded ones, its password, confirmed MFA factors, and passkeys.

        Returns:
            Tuple of viable ``LoginMethod`` entries for ``account_id``.
        """
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            return await services.list_login_methods(account_id)

    async def register_login_method(
        self,
        account_id: str,
        method: LoginMethod,
        *,
        event: SecurityEvent,
    ) -> None:
        """Persist a login method record for an account together with its audit event."""
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            await services.login_methods.record(account_id, method)
            await services.audit_logs.create(security_audit_record(event), auto_commit=True)

    async def revoke_login_method(
        self,
        account_id: str,
        method_id: str,
        *,
        require_remaining: bool = True,
        event: SecurityEvent,
    ) -> RevokeLoginMethodOutcome:
        """Revoke one login method with its MFA factor or passkey and record the audit event atomically.

        The account stays locked for the transaction, so concurrent revocations cannot each remove a
        different method and leave the account without any.

        Returns:
            ``RevokeLoginMethodOutcome`` indicating ``REVOKED``, ``NOT_FOUND``, or ``FINAL_METHOD``.
        """
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            status = await services.revoke_login_method(account_id, method_id, require_remaining=require_remaining)
            if status is RevokeLoginMethodStatus.REVOKED:
                await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return RevokeLoginMethodOutcome(status)

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
        """Provision an account, consume its invitation, store its verification token, and record the audit event.

        Everything commits together; any outcome other than ``CREATED`` leaves the database untouched, as does
        the ``ValueError`` that ``PurposeTokenService.issue`` raises for a colliding verification token identifier.

        Returns:
            ``RegistrationOutcome`` with status and created account state when successful.
        """
        notification: NotificationCommand | None = None
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            user_or_rejection = await services.register_account(
                command,
                password_hash,
                invitation_digest=invitation_digest,
                verified=verification is None,
                now=now,
            )
            if isinstance(user_or_rejection, RegistrationStatus):
                return RegistrationOutcome(user_or_rejection)
            user = user_or_rejection
            if verification is not None:
                token_issue, notification = verification.bind(str(user.id))
                await services.purpose_tokens.issue(token_issue, user_id=user.id)
            await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            account = services.users.to_account_state(await services.users.reload_for_authorization(user))

        if notification is not None:
            await self._notify(notification)
        return RegistrationOutcome(RegistrationStatus.CREATED, account)

    async def issue(
        self,
        issue: TokenIssue,
        notification: NotificationCommand,
        *,
        event: SecurityEvent,
    ) -> None:
        """Persist a single-use purpose token digest with its audit event, then dispatch its notification.

        A colliding ``issue.token_id`` surfaces as the ``ValueError`` raised by ``PurposeTokenService.issue``.
        """
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            await services.purpose_tokens.issue(issue, user_id=UserService.to_user_id(issue.account_id))
            await services.audit_logs.create(security_audit_record(event), auto_commit=True)
        await self._notify(notification)

    async def issue_absent(self) -> None:
        """Perform a constant-interface no-op when issuing for a non-existent account."""

    async def consume_and_verify(
        self,
        token_id: str,
        digest: bytes,
        *,
        now: datetime,
        event: SecurityEvent,
    ) -> VerificationOutcome:
        """Atomically consume a verification token, mark its account verified, and record the audit event.

        Returns:
            ``VerificationOutcome`` with consumption status and updated account metadata.
        """
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            user_or_rejection = await services.redeem_purpose_token(
                token_id,
                digest,
                purpose=TokenPurpose.VERIFICATION,
                now=now,
            )
            if isinstance(user_or_rejection, str):
                return VerificationOutcome(_VERIFICATION_REJECTIONS[user_or_rejection])
            user = await services.users.update(
                {"is_verified": True, "verified_at": now.date()},
                item_id=user_or_rejection.id,
            )
            await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return VerificationOutcome(VerificationStatus.CONSUMED, str(user.id), user.security_epoch)

    async def consume_and_reset(
        self,
        token_id: str,
        digest: bytes,
        new_password_hash: str,
        *,
        now: datetime,
        event: SecurityEvent,
    ) -> PasswordResetOutcome:
        """Atomically consume a recovery token, replace the password, bump the epoch, and record the audit event.

        Returns:
            ``PasswordResetOutcome`` with reset status and next security epoch.
        """
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            user_or_rejection = await services.redeem_purpose_token(
                token_id,
                digest,
                purpose=TokenPurpose.RECOVERY,
                now=now,
            )
            if isinstance(user_or_rejection, str):
                return PasswordResetOutcome(_PASSWORD_RESET_REJECTIONS[user_or_rejection])
            user = user_or_rejection
            issued_epoch = user.security_epoch
            password_replaced = await services.users.replace_password_hash_and_bump_epoch(
                user.id,
                new_password_hash,
                expected_epoch=issued_epoch,
                reset_at=now,
            )
            if not password_replaced:
                return PasswordResetOutcome(PasswordResetStatus.CONFLICT)
            await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return PasswordResetOutcome(PasswordResetStatus.RESET, str(user.id), issued_epoch + 1)

    async def create(
        self,
        command: CreateSessionCommand,
        *,
        event: SecurityEvent,
    ) -> UserAuthSession:
        """Persist a new authenticated browser session together with its audit event.

        A non-UUID ``command.account_id`` or a colliding ``session_id`` surfaces as the ``ValueError`` raised
        by ``UserSessionService.start``.

        Returns:
            Persisted ``UserAuthSession`` record.
        """
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            user_session = await services.user_sessions.start(command)
            await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return services.user_sessions.to_auth_session(user_session)

    async def get(self, session_id: str) -> UserAuthSession | None:
        """Return an active, unexpired session record or ``None``."""
        async with UserSessionService.new(config=self._alchemy_config) as user_sessions:
            user_session = await user_sessions.find_active(session_id, now=self._clock())
            return user_sessions.to_auth_session(user_session) if user_session is not None else None

    async def list_for_account(self, account_id: str) -> tuple[UserAuthSession, ...]:
        """List active, unexpired sessions for one user account.

        Returns:
            Tuple of active ``UserAuthSession`` records for ``account_id``.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return ()
        async with UserSessionService.new(config=self._alchemy_config) as user_sessions:
            active_sessions = await user_sessions.list_active_for_user(user_id, now=self._clock())
            return tuple(user_sessions.to_auth_session(user_session) for user_session in active_sessions)

    async def touch(self, session_id: str, *, now: datetime) -> UserAuthSession | None:
        """Advance ``last_seen_at`` on a session that is active both at ``now`` and on the backend's clock.

        Returns:
            Updated ``UserAuthSession``, or ``None`` if the session is missing, revoked, or expired.
        """
        latest_instant = max(now, self._clock())
        async with UserSessionService.new(config=self._alchemy_config) as user_sessions:
            user_session = await user_sessions.find_active(session_id, now=latest_instant)
            if user_session is None or not await user_sessions.mark_seen(user_session, now=now):
                return None
            await user_sessions.repository.session.commit()
            return user_sessions.to_auth_session(user_session)

    async def revoke_session_for_account(
        self,
        account_id: str,
        session_id: str,
        *,
        event: SecurityEvent,
    ) -> bool:
        """Revoke one session owned by the given account and record the audit event.

        Returns:
            ``True`` if an active session was revoked, ``False`` otherwise.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return False
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            revoked = await services.user_sessions.revoke_for_user(user_id, session_id, now=self._clock())
            if revoked:
                await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return revoked

    async def revoke_sessions_for_account(
        self,
        account_id: str,
        *,
        event: SecurityEvent,
    ) -> int:
        """Revoke all active sessions owned by the given account and record the audit event.

        Returns:
            Number of sessions revoked.
        """
        return await self._revoke_all_sessions(account_id, keep_session_id=None, event=event)

    async def revoke_other_sessions(
        self,
        account_id: str,
        session_id: str,
        *,
        event: SecurityEvent,
    ) -> int:
        """Revoke all active sessions for an account except the specified current session.

        Returns:
            Number of sessions revoked.
        """
        return await self._revoke_all_sessions(account_id, keep_session_id=session_id, event=event)

    async def rebind(
        self,
        prior_session_id: str,
        command: CreateSessionCommand,
        *,
        event: SecurityEvent,
    ) -> UserAuthSession | None:
        """Atomically replace a prior active session with a successor session and record the audit event.

        A colliding replacement ``session_id`` surfaces as the ``ValueError`` raised by
        ``UserSessionService.start``.

        Returns:
            Persisted successor ``UserAuthSession``, or ``None`` if the prior session is inactive or invalid.
        """
        if UserService.to_user_id(command.account_id) is None:
            return None
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            if not await services.user_sessions.revoke(prior_session_id, now=self._clock()):
                return None
            user_session = await services.user_sessions.start(command)
            await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return services.user_sessions.to_auth_session(user_session)

    async def resolve_user_auth_session(
        self,
        session_id: str,
        account_id: str,
        *,
        now: datetime,
    ) -> ResolvedUserAuthSession[m.User] | None:
        """Resolve an active session and its eager-loaded user in one query.

        Database errors propagate to ``NativeSessionAuth.authenticate`` which
        fails closed with ``VerificationUnavailable``.

        Returns:
            ``ResolvedUserAuthSession`` if session and user are active, otherwise ``None``.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return None
        async with UserSessionService.new(config=self._alchemy_config) as user_sessions:
            user_session = await user_sessions.find_active_with_user(session_id, user_id, now=now)
            if user_session is None:
                return None
            return ResolvedUserAuthSession(
                session=user_sessions.to_auth_session(user_session),
                account=UserService.to_account_state(user_session.user),
            )

    async def resolve_session(
        self,
        session_id: str,
        account_id: str,
        *,
        now: datetime | None = None,
    ) -> ResolvedUserAuthSession[m.User] | InvalidCredentials | VerificationUnavailable:
        """Fail-closed session lookup converting storage errors to ``VerificationUnavailable``.

        Returns:
            Resolved session, ``InvalidCredentials`` if not found/expired, or ``VerificationUnavailable``.
        """
        try:
            resolved = await self.resolve_user_auth_session(
                session_id,
                account_id,
                now=now if now is not None else self._clock(),
            )
        except (SQLAlchemyError, RepositoryError):
            logger.warning("Database error during session resolution", session_id=session_id)
            return VerificationUnavailable()
        if resolved is None:
            return InvalidCredentials()
        return resolved

    async def _find_account(self, criterion: ColumnElement[bool]) -> LocalAccountState[m.User] | None:
        async with UserService.new(config=self._alchemy_config) as users:
            user = await users.find_for_authorization(criterion)
            return users.to_account_state(user) if user is not None else None

    async def _notify(self, notification: NotificationCommand) -> None:
        if self._notification_handler is not None:
            await self._notification_handler(notification)

    async def _revoke_all_sessions(self, account_id: str, *, keep_session_id: str | None, event: SecurityEvent) -> int:
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return 0
        async with AccountSecurityServices.new(config=self._alchemy_config) as services:
            revoked_count = await services.user_sessions.revoke_all_for_user(
                user_id,
                now=self._clock(),
                keep_session_id=keep_session_id,
            )
            if revoked_count:
                await services.audit_logs.create(security_audit_record(event), auto_commit=True)
            return revoked_count
