"""Browser session, purpose token, and login method database services."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from advanced_alchemy.exceptions import IntegrityError
from advanced_alchemy.extensions.litestar import service
from litestar_security.accounts import CreateSessionCommand, LoginMethod, TokenPurpose, UserAuthSession
from sqlalchemy import case, literal, update
from sqlalchemy.orm import joinedload

from app.db import models as m
from app.domain.accounts.services._statements import ACCOUNT_STATE_LOAD, affected_rows, is_constraint_violation

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.service import ModelDictT
    from litestar_security.accounts import TokenIssue
    from sqlalchemy import ColumnElement

TokenRejection = Literal["invalid", "used", "expired", "conflict"]
"""Why a purpose token could not be redeemed."""

LOGIN_METHODS_NAMESPACE = "login_methods"
_PERMANENT_STORE_EXPIRY = datetime(9999, 12, 31, tzinfo=UTC)
_SESSION_COLLISION = "Session identifier collision"
_ISSUE_COLLISION = "Purpose token identifier collision"


class UserSessionService(service.SQLAlchemyAsyncRepositoryService[m.UserSession]):
    """Handles database operations for server-side browser sessions."""

    async def to_model_on_create(self, data: ModelDictT[m.UserSession]) -> ModelDictT[m.UserSession]:
        """Translate a ``CreateSessionCommand`` into the browser session stored for its account.

        Returns:
            The browser session to persist, or ``data`` unchanged when it is not a ``CreateSessionCommand``.
        """
        if not isinstance(data, CreateSessionCommand):
            return data
        return m.UserSession(
            session_id=data.session_id,
            binding_id=data.binding_id,
            binding_digest=data.binding_digest.hex(),
            user_id=UUID(data.account_id),
            security_epoch=data.security_epoch,
            created_at=data.created_at,
            updated_at=data.created_at,
            authenticated_at=data.authenticated_at,
            last_seen_at=data.created_at,
            expires_at=data.expires_at,
            display_metadata=dict(data.display_metadata),
        )

    @staticmethod
    def to_auth_session(user_session: m.UserSession) -> UserAuthSession:
        """Translate a stored browser session into the ``UserAuthSession`` the security library works with.

        Returns:
            Session record carrying the binding, owner, epoch, and lifetime.
        """
        return UserAuthSession(
            session_id=user_session.session_id,
            binding_id=user_session.binding_id,
            binding_digest=bytes.fromhex(user_session.binding_digest),
            account_id=str(user_session.user_id),
            security_epoch=user_session.security_epoch,
            created_at=user_session.created_at,
            authenticated_at=user_session.authenticated_at,
            last_seen_at=user_session.last_seen_at,
            expires_at=user_session.expires_at,
            display_metadata=dict(user_session.display_metadata or {}),
        )

    async def find_active(self, session_id: str, *, now: datetime) -> m.UserSession | None:
        """Load a browser session that is neither revoked nor expired at ``now``.

        Returns:
            The active browser session, or ``None`` when it is unknown, revoked, or expired.
        """
        user_session = await self.get_one_or_none(
            m.UserSession.session_id == session_id,
            m.UserSession.revoked_at.is_(None),
        )
        if user_session is None or user_session.expires_at <= now:
            return None
        return user_session

    async def find_active_with_user(self, session_id: str, user_id: UUID, *, now: datetime) -> m.UserSession | None:
        """Load an active browser session owned by ``user_id`` together with its user in one query.

        The user arrives with the relationships ``UserService.to_account_state`` exposes.

        Returns:
            The active browser session, or ``None`` when it is unknown, revoked, expired, or owned by another user.
        """
        user_session = await self.get_one_or_none(
            m.UserSession.session_id == session_id,
            m.UserSession.user_id == user_id,
            m.UserSession.revoked_at.is_(None),
            load=[joinedload(m.UserSession.user, innerjoin=True).options(*ACCOUNT_STATE_LOAD)],
        )
        if user_session is None or user_session.expires_at <= now:
            return None
        return user_session

    async def list_active_for_user(self, user_id: UUID, *, now: datetime) -> list[m.UserSession]:
        """List the user's browser sessions that are neither revoked nor expired at ``now``.

        Returns:
            Active browser sessions owned by ``user_id``.
        """
        user_sessions = await self.list(m.UserSession.user_id == user_id, m.UserSession.revoked_at.is_(None))
        return [user_session for user_session in user_sessions if user_session.expires_at > now]

    async def start(self, command: CreateSessionCommand) -> m.UserSession:
        """Store a newly authenticated browser session inside the caller's transaction.

        Returns:
            The stored browser session.

        Raises:
            ValueError: If ``command.account_id`` is not a UUID or the session identifier is already taken.
            IntegrityError: If the database fails for a reason other than a violated constraint.
        """
        try:
            return await self.create(command)
        except IntegrityError as error:
            if not is_constraint_violation(error):
                raise
            raise ValueError(_SESSION_COLLISION) from error

    async def mark_seen(self, user_session: m.UserSession, *, now: datetime) -> bool:
        """Advance ``last_seen_at`` only while the browser session is still unrevoked.

        Returns:
            ``True`` when the browser session was updated, ``False`` when it was revoked in the meantime.
        """
        statement = (
            update(m.UserSession)
            .where(m.UserSession.id == user_session.id, m.UserSession.revoked_at.is_(None))
            .values(last_seen_at=now)
        )
        return await affected_rows(self.repository.session, statement) == 1

    async def revoke(self, session_id: str, *, now: datetime) -> bool:
        """Revoke one browser session that is not already revoked.

        Returns:
            ``True`` when this call revoked the browser session, ``False`` when it was unknown or already revoked.
        """
        return await self._revoke_where(m.UserSession.session_id == session_id, now=now) == 1

    async def revoke_for_user(self, user_id: UUID, session_id: str, *, now: datetime) -> bool:
        """Revoke one browser session only when ``user_id`` owns it.

        Returns:
            ``True`` when this call revoked the browser session, ``False`` when it was unknown, already
            revoked, or owned by another user.
        """
        revoked_count = await self._revoke_where(
            m.UserSession.user_id == user_id,
            m.UserSession.session_id == session_id,
            now=now,
        )
        return revoked_count == 1

    async def revoke_all_for_user(self, user_id: UUID, *, now: datetime, keep_session_id: str | None = None) -> int:
        """Revoke every unrevoked browser session the user owns, optionally keeping one.

        Returns:
            Number of browser sessions revoked.
        """
        if keep_session_id is None:
            return await self._revoke_where(m.UserSession.user_id == user_id, now=now)
        return await self._revoke_where(
            m.UserSession.user_id == user_id,
            m.UserSession.session_id != keep_session_id,
            now=now,
        )

    async def _revoke_where(self, *criteria: ColumnElement[bool], now: datetime) -> int:
        statement = update(m.UserSession).where(*criteria, m.UserSession.revoked_at.is_(None)).values(revoked_at=now)
        return await affected_rows(self.repository.session, statement)


class PurposeTokenService(service.SQLAlchemyAsyncRepositoryService[m.PurposeToken]):
    """Handles database operations for verification, recovery, and invitation tokens."""

    async def issue(self, token_issue: TokenIssue, *, user_id: UUID | None) -> m.PurposeToken:
        """Store the digest of a newly issued token inside the caller's transaction.

        Args:
            token_issue: Token digest, purpose, account binding, and expiry to store.
            user_id: Account the token belongs to, or ``None`` when it is not bound to an existing account.

        Returns:
            The stored purpose token.

        Raises:
            ValueError: If a purpose token with the same identifier already exists.
        """
        if await self.exists(token_id=token_issue.token_id):
            raise ValueError(_ISSUE_COLLISION)
        return await self.create(
            m.PurposeToken(
                token_id=token_issue.token_id,
                token_hash=token_issue.digest.hex(),
                purpose=token_issue.purpose.value,
                user_id=user_id,
                account_ref=token_issue.account_id,
                issued_security_epoch=token_issue.issued_security_epoch,
                attempts=0,
                maximum_attempts=token_issue.maximum_attempts,
                expires_at=token_issue.expires_at,
            )
        )

    async def redeem_invitation(self, digest: bytes, *, now: datetime) -> bool:
        """Burn the unconsumed, unrevoked, unexpired invitation stored under ``digest``.

        Returns:
            ``True`` when this call burned the invitation, ``False`` when no usable invitation matched.
        """
        invitation = await self.get_one_or_none(
            m.PurposeToken.purpose == TokenPurpose.INVITATION.value,
            m.PurposeToken.token_hash == digest.hex(),
            m.PurposeToken.consumed_at.is_(None),
            m.PurposeToken.revoked_at.is_(None),
        )
        if invitation is None or invitation.expires_at <= now:
            return False
        return await self.burn(invitation, now=now)

    async def burn(self, purpose_token: m.PurposeToken, *, now: datetime) -> bool:
        """Mark an unconsumed token as consumed.

        Returns:
            ``True`` when this call consumed the token, ``False`` when it was already consumed.
        """
        statement = (
            update(m.PurposeToken)
            .where(m.PurposeToken.id == purpose_token.id, m.PurposeToken.consumed_at.is_(None))
            .values(consumed_at=now)
        )
        return await affected_rows(self.repository.session, statement) == 1

    async def record_failed_attempt(self, purpose_token: m.PurposeToken, *, now: datetime) -> None:
        """Count one failed proof in a single statement, consuming the token on its last allowed attempt."""
        attempts = m.PurposeToken.attempts + 1
        is_last_attempt = m.PurposeToken.consumed_at.is_(None) & (attempts >= m.PurposeToken.maximum_attempts)
        consumed_at = case(
            (is_last_attempt, literal(now, m.PurposeToken.consumed_at.type)),
            else_=m.PurposeToken.consumed_at,
        )
        statement = (
            update(m.PurposeToken)
            .where(m.PurposeToken.id == purpose_token.id)
            .values(attempts=attempts, consumed_at=consumed_at)
        )
        await affected_rows(self.repository.session, statement)


class LoginMethodService(service.SQLAlchemyAsyncRepositoryService[m.AppStore]):
    """Handles login methods recorded per account in the shared key-value store."""

    @staticmethod
    def to_login_method(recorded_method: m.AppStore) -> LoginMethod:
        """Translate a recorded entry back into its ``LoginMethod``.

        Returns:
            The login method that was recorded.
        """
        recorded = json.loads(recorded_method.value)
        return LoginMethod(
            method_id=recorded["method_id"],
            kind=recorded["kind"],
            created_at=datetime.fromisoformat(recorded["created_at"]),
            display_name=recorded.get("display_name"),
        )

    async def list_for_account(self, account_id: str) -> Sequence[m.AppStore]:
        """List the login methods recorded for one account.

        Returns:
            Recorded entries whose key belongs to ``account_id``.
        """
        return await self.list(
            m.AppStore.namespace == LOGIN_METHODS_NAMESPACE,
            m.AppStore.key.startswith(f"{account_id}:"),
        )

    async def find_recorded(self, account_id: str, method_id: str) -> m.AppStore | None:
        """Load the entry recorded for one of the account's login methods.

        Returns:
            The recorded entry, or ``None`` when the account never recorded ``method_id``.
        """
        return await self.get_one_or_none(
            m.AppStore.namespace == LOGIN_METHODS_NAMESPACE,
            m.AppStore.key == f"{account_id}:{method_id}",
        )

    async def record(self, account_id: str, login_method: LoginMethod) -> None:
        """Insert or replace one recorded login method inside the caller's transaction."""
        serialized_method = json.dumps(
            {
                "method_id": login_method.method_id,
                "kind": login_method.kind,
                "created_at": login_method.created_at.isoformat(),
                "display_name": login_method.display_name,
            }
        ).encode("utf-8")
        recorded_method = await self.find_recorded(account_id, login_method.method_id)
        if recorded_method is not None:
            recorded_method.value = serialized_method
            return
        await self.create(
            m.AppStore(
                namespace=LOGIN_METHODS_NAMESPACE,
                key=f"{account_id}:{login_method.method_id}",
                value=serialized_method,
                expires_at=_PERMANENT_STORE_EXPIRY,
            )
        )
