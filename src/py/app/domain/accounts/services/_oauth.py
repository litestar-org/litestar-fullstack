"""Linked OAuth account and OAuth transaction database services."""

from __future__ import annotations

from hmac import compare_digest
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.exceptions import IntegrityError
from advanced_alchemy.extensions.litestar import service
from litestar_security.providers.oauth import (
    AccountLinkError,
    LinkedProviderAccount,
    OAuthOperation,
    OAuthTransaction,
    ProviderGrant,
    ProviderTokenReference,
    StoredProviderTokens,
)
from sqlalchemy import delete, update

from app.db import models as m
from app.domain.accounts.services._statements import affected_rows, is_constraint_violation
from app.domain.accounts.services._user import UserService

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from litestar_security.providers.oauth import ProtectedOAuthSecret, ProviderIdentity, ProviderTokenSet, SecretStr


class OAuthAccountService(service.SQLAlchemyAsyncRepositoryService[m.UserOAuthAccount]):
    """Handles database operations for linked provider accounts and their protected tokens."""

    @staticmethod
    def to_oauth_account_id(provider_account_id: str) -> UUID | None:
        """Translate the security library's provider account identifier into the linked account's primary key.

        This is the inverse of the ``provider_account_id=str(oauth_account.id)`` that ``to_linked_account``
        hands the library.

        Returns:
            The linked account identifier, or ``None`` when ``provider_account_id`` does not name one.
        """
        try:
            return UUID(provider_account_id)
        except ValueError:
            return None

    @staticmethod
    def to_account_email(identity: ProviderIdentity) -> str:
        """Choose the email address an account provisioned for a provider identity is stored under.

        An identity without an email address gets a placeholder at ``oauth.local``. The placeholder spells the
        subject as the hexadecimal of its UTF-8 bytes, so subjects that differ only by letter case stay
        distinct once the address is normalized.

        Returns:
            The identity's email address, or its placeholder.
        """
        return identity.email or f"{identity.provider}-{identity.subject.encode().hex()}@oauth.local"

    @staticmethod
    def to_linked_account(oauth_account: m.UserOAuthAccount) -> LinkedProviderAccount:
        """Translate a linked account into the ``LinkedProviderAccount`` the security library works with.

        Returns:
            The provider link with its current grant.
        """
        return LinkedProviderAccount(
            provider_account_id=str(oauth_account.id),
            account_id=str(oauth_account.user_id),
            provider=oauth_account.oauth_name,
            issuer=oauth_account.issuer or "",
            subject=oauth_account.account_id,
            grant=ProviderGrant(
                scopes=frozenset(oauth_account.scopes or ()),
                expires_at=oauth_account.token_expires_at or oauth_account.created_at,
            ),
            linked_at=oauth_account.created_at,
        )

    @staticmethod
    def to_stored_tokens(oauth_account: m.UserOAuthAccount, tokens: ProviderTokenSet) -> StoredProviderTokens:
        """Pair decrypted tokens with the version reference a later compare-and-swap must present.

        Returns:
            The tokens and their versioned reference.
        """
        reference = ProviderTokenReference(
            provider_account_id=str(oauth_account.id),
            version=oauth_account.token_version,
            scopes=frozenset(oauth_account.scopes or ()),
            expires_at=oauth_account.token_expires_at or tokens.expires_at,
        )
        return StoredProviderTokens(reference=reference, tokens=tokens)

    async def find_by_identity(self, identity: ProviderIdentity) -> m.UserOAuthAccount | None:
        """Load the linked account for a provider identity, whoever owns it.

        Returns:
            The linked account, or ``None`` when the identity has never been linked.
        """
        return await self.get_one_or_none(oauth_name=identity.provider, account_id=identity.subject)

    async def find_owned(self, oauth_account_id: UUID, *, user_id: UUID, provider: str) -> m.UserOAuthAccount | None:
        """Load one of a user's linked accounts for the named provider.

        Returns:
            The linked account, or ``None`` when it is unknown, owned by another user, or from another provider.
        """
        return await self.get_one_or_none(id=oauth_account_id, user_id=user_id, oauth_name=provider)

    async def list_expiring(self, *, before: datetime) -> Sequence[m.UserOAuthAccount]:
        """List linked accounts whose retained tokens expire at or before ``before``.

        Returns:
            Linked accounts holding tokens that are due for a refresh.
        """
        return await self.list(
            m.UserOAuthAccount.protected_tokens.is_not(None),
            m.UserOAuthAccount.token_expires_at.is_not(None),
            m.UserOAuthAccount.token_expires_at <= before,
        )

    async def link(
        self,
        user_id: UUID,
        identity: ProviderIdentity,
        *,
        grant: ProviderGrant,
        protected_tokens: ProtectedOAuthSecret | None,
        now: datetime,
    ) -> m.UserOAuthAccount:
        """Link a provider identity to a user, renewing the grant when the user already holds that link.

        Args:
            user_id: Account the identity is linked to.
            identity: Provider identity being linked.
            grant: Scopes and expiry the provider granted.
            protected_tokens: Encrypted tokens to retain, or ``None`` to retain none.
            now: Timestamp of the provider exchange.

        Returns:
            The linked account.

        Raises:
            AccountLinkError: If the identity belongs to another user, or the user already linked a different
                identity of the same provider.
        """
        oauth_account = await self.find_by_identity(identity)
        if oauth_account is None:
            return await self.create_link(
                user_id,
                identity,
                email=identity.email or "",
                grant=grant,
                protected_tokens=protected_tokens,
                now=now,
            )
        if oauth_account.user_id != user_id:
            raise AccountLinkError
        await self.replace_grant(
            oauth_account,
            grant=grant,
            protected_tokens=protected_tokens,
            now=now,
            issuer=identity.issuer,
        )
        return oauth_account

    async def create_link(
        self,
        user_id: UUID,
        identity: ProviderIdentity,
        *,
        email: str,
        grant: ProviderGrant,
        protected_tokens: ProtectedOAuthSecret | None,
        now: datetime,
    ) -> m.UserOAuthAccount:
        """Store a new link between a provider identity and a user inside the caller's transaction.

        Args:
            user_id: Owner of the new link.
            identity: Provider identity being linked.
            email: Email address recorded for the linked identity.
            grant: Scopes and expiry the provider granted.
            protected_tokens: Encrypted tokens to retain, or ``None`` to retain none.
            now: Timestamp of the provider exchange.

        Returns:
            The flushed linked account.

        Raises:
            AccountLinkError: If the identity is already linked, the user already linked the provider, or
                the user does not exist.
            IntegrityError: If the database fails for a reason other than a violated constraint.
        """
        try:
            return await self.create(
                m.UserOAuthAccount(
                    user_id=user_id,
                    oauth_name=identity.provider,
                    issuer=identity.issuer,
                    account_id=identity.subject,
                    account_email=email,
                    protected_tokens=protected_tokens.ciphertext if protected_tokens is not None else None,
                    key_version=protected_tokens.key_version if protected_tokens is not None else None,
                    token_version=1,
                    scopes=sorted(grant.scopes),
                    token_expires_at=grant.expires_at,
                    provider_user_data=dict(identity.raw_claims) if identity.raw_claims else None,
                    last_login_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
        except IntegrityError as error:
            if not is_constraint_violation(error):
                raise
            raise AccountLinkError from error

    async def replace_grant(
        self,
        oauth_account: m.UserOAuthAccount,
        *,
        grant: ProviderGrant,
        protected_tokens: ProtectedOAuthSecret | None,
        now: datetime,
        issuer: str | None = None,
    ) -> None:
        """Overwrite a linked account's grant and retained tokens after a completed provider exchange.

        The token version advances with every replacement, so a writer still holding the previous version
        fails its next compare-and-swap instead of overwriting these tokens.

        Args:
            oauth_account: Linked account receiving the new grant.
            grant: Scopes and expiry the provider granted.
            protected_tokens: Encrypted tokens to retain, or ``None`` to drop any retained tokens.
            now: Timestamp of the provider exchange.
            issuer: Issuer to record, or ``None`` to keep the stored issuer.

        Raises:
            AccountLinkError: If the linked account no longer exists.
        """
        statement = (
            update(m.UserOAuthAccount)
            .where(m.UserOAuthAccount.id == oauth_account.id)
            .values(
                scopes=sorted(grant.scopes),
                token_expires_at=grant.expires_at,
                protected_tokens=protected_tokens.ciphertext if protected_tokens is not None else None,
                key_version=protected_tokens.key_version if protected_tokens is not None else None,
                token_version=m.UserOAuthAccount.token_version + 1,
                last_login_at=now,
                updated_at=now,
            )
        )
        if issuer is not None:
            statement = statement.values(issuer=issuer)
        if await affected_rows(self.repository.session, statement) != 1:
            raise AccountLinkError

    async def replace_tokens(
        self,
        oauth_account: m.UserOAuthAccount,
        *,
        expected_version: int,
        tokens: ProviderTokenSet,
        protected_tokens: ProtectedOAuthSecret,
    ) -> bool:
        """Store refreshed tokens only while the stored token version still equals ``expected_version``.

        Returns:
            ``True`` when the tokens were replaced, ``False`` when another writer advanced the version first.
        """
        statement = (
            update(m.UserOAuthAccount)
            .where(
                m.UserOAuthAccount.id == oauth_account.id,
                m.UserOAuthAccount.token_version == expected_version,
            )
            .values(
                protected_tokens=protected_tokens.ciphertext,
                key_version=protected_tokens.key_version,
                token_version=expected_version + 1,
                scopes=sorted(tokens.scopes),
                token_expires_at=tokens.expires_at,
            )
        )
        return await affected_rows(self.repository.session, statement) == 1

    async def discard_tokens(self, oauth_account_id: UUID, *, expected_version: int | None) -> bool:
        """Clear retained tokens and advance the token version, optionally only at ``expected_version``.

        Returns:
            ``True`` when the tokens were cleared, ``False`` when the account is missing or its version moved.
        """
        statement = (
            update(m.UserOAuthAccount)
            .where(m.UserOAuthAccount.id == oauth_account_id)
            .values(protected_tokens=None, key_version=None, token_version=m.UserOAuthAccount.token_version + 1)
        )
        if expected_version is not None:
            statement = statement.where(m.UserOAuthAccount.token_version == expected_version)
        return await affected_rows(self.repository.session, statement) == 1

    async def unlink(self, oauth_account: m.UserOAuthAccount) -> bool:
        """Remove a linked account together with its grant and retained tokens.

        Returns:
            ``True`` when this call removed the link, ``False`` when it was already gone.
        """
        statement = delete(m.UserOAuthAccount).where(m.UserOAuthAccount.id == oauth_account.id)
        return await affected_rows(self.repository.session, statement) == 1


class OAuthTransactionService(service.SQLAlchemyAsyncRepositoryService[m.OAuthTransaction]):
    """Handles database operations for single-use OAuth authorization transactions."""

    @staticmethod
    def to_transaction(
        oauth_transaction: m.OAuthTransaction,
        *,
        pkce_verifier: SecretStr,
        nonce: SecretStr | None,
    ) -> OAuthTransaction:
        """Translate a stored transaction into the ``OAuthTransaction`` it was recorded from.

        Returns:
            The transaction as the provider callback expects it, carrying its decrypted secrets.
        """
        return OAuthTransaction(
            state_digest=bytes.fromhex(oauth_transaction.state_hash),
            binding_digest=bytes.fromhex(oauth_transaction.binding_digest),
            operation=OAuthOperation(oauth_transaction.operation),
            provider=oauth_transaction.provider,
            expected_issuer=oauth_transaction.expected_issuer,
            redirect_uri=oauth_transaction.redirect_uri,
            return_to=oauth_transaction.return_to or "/",
            requested_scopes=frozenset(oauth_transaction.requested_scopes),
            pkce_verifier=pkce_verifier,
            nonce=nonce,
            account_id=str(oauth_transaction.user_id) if oauth_transaction.user_id is not None else None,
            session_binding=oauth_transaction.session_binding,
            security_epoch=oauth_transaction.security_epoch,
            provider_account_id=oauth_transaction.provider_account_id,
            step_up_purpose=oauth_transaction.step_up_purpose,
            maximum_authentication_age=oauth_transaction.maximum_authentication_age,
            expires_at=oauth_transaction.expires_at,
        )

    async def record(
        self,
        transaction: OAuthTransaction,
        *,
        protected_secrets: ProtectedOAuthSecret,
    ) -> m.OAuthTransaction:
        """Store a pending transaction with its PKCE verifier and nonce already encrypted.

        Returns:
            The flushed transaction.
        """
        return await self.create(
            m.OAuthTransaction(
                state_hash=transaction.state_digest.hex(),
                binding_digest=transaction.binding_digest.hex(),
                operation=transaction.operation.value,
                provider=transaction.provider,
                expected_issuer=transaction.expected_issuer,
                redirect_uri=transaction.redirect_uri,
                return_to=transaction.return_to,
                requested_scopes=sorted(transaction.requested_scopes),
                protected_payload=protected_secrets.ciphertext,
                key_version=protected_secrets.key_version,
                user_id=UserService.to_user_id(transaction.account_id),
                session_binding=transaction.session_binding,
                security_epoch=transaction.security_epoch,
                provider_account_id=transaction.provider_account_id,
                step_up_purpose=transaction.step_up_purpose,
                maximum_authentication_age=transaction.maximum_authentication_age,
                expires_at=transaction.expires_at,
            )
        )

    async def redeem(
        self,
        state_digest: bytes,
        *,
        binding_digest: bytes,
        provider: str,
        now: datetime,
    ) -> m.OAuthTransaction | None:
        """Burn an unconsumed transaction only when it was issued for this provider callback.

        A callback with a wrong provider or binding, or one arriving after expiry, leaves the transaction
        unconsumed.

        Returns:
            The transaction when provider, binding, and expiry all match and this call burned it, otherwise
            ``None``.
        """
        oauth_transaction = await self.get_one_or_none(
            m.OAuthTransaction.consumed_at.is_(None),
            state_hash=state_digest.hex(),
        )
        if oauth_transaction is None:
            return None
        issued_for_callback = (
            oauth_transaction.provider == provider
            and compare_digest(bytes.fromhex(oauth_transaction.binding_digest), binding_digest)
            and oauth_transaction.expires_at > now
        )
        if not issued_for_callback or not await self._burn(oauth_transaction, now=now):
            return None
        return oauth_transaction

    async def _burn(self, oauth_transaction: m.OAuthTransaction, *, now: datetime) -> bool:
        statement = (
            update(m.OAuthTransaction)
            .where(m.OAuthTransaction.id == oauth_transaction.id, m.OAuthTransaction.consumed_at.is_(None))
            .values(consumed_at=now)
        )
        return await affected_rows(self.repository.session, statement) == 1
