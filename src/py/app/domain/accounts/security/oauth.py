"""Persistence adapters for ``litestar-security`` OAuth transactions and linked accounts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from litestar_security.providers.oauth import (
    AccountLinkError,
    AESGCMOAuthTransactionProtector,
    LinkedProviderAccount,
    OAuthAccountError,
    OAuthLoginOutcome,
    OAuthRevocationFailure,
    OAuthTransaction,
    OAuthTransactionProtector,
    OAuthTransactionProtectorKey,
    ProtectedOAuthSecret,
    ProviderGrant,
    ProviderIdentity,
    ProviderTokenSet,
    SecretStr,
    StoredProviderTokens,
    UnlinkOutcome,
    UnlinkStatus,
)

from app.domain.accounts.services import OAuthAccountService, OAuthServices, OAuthTransactionService, UserService
from app.lib.secrets import OAUTH_PROTECTOR_INFO, derive_subkey

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

    from app.db import models as m
    from app.lib.settings import Settings

__all__ = (
    "SQLAlchemyOAuthAccountStore",
    "SQLAlchemyOAuthTransactionStore",
    "build_oauth_protector",
    "deserialize_oauth_tokens",
    "oauth_account_aad",
    "serialize_oauth_tokens",
)


def oauth_account_aad(provider: str, subject: str) -> bytes:
    """Build canonical AEAD associated data for persisted ``UserOAuthAccount`` tokens.

    Returns:
        UTF-8 encoded associated data bytes binding ``provider`` and ``subject``.
    """
    return f"oauth_account|{provider}|{subject}".encode()


def build_oauth_protector(
    settings: Settings,
    *,
    key_version: str = "v1",
    retained_keys: Sequence[OAuthTransactionProtectorKey] = (),
) -> AESGCMOAuthTransactionProtector:
    """Build an ``AESGCMOAuthTransactionProtector`` using an HKDF-derived 32-byte key.

    Returns:
        Configured ``AESGCMOAuthTransactionProtector`` instance.
    """
    active = OAuthTransactionProtectorKey(
        key_version=key_version,
        key=derive_subkey(settings.app.SECRET_KEY, OAUTH_PROTECTOR_INFO),
    )
    return AESGCMOAuthTransactionProtector(active_key=active, retained_keys=tuple(retained_keys))


def serialize_oauth_tokens(tokens: ProviderTokenSet) -> bytes:
    """Serialize a ``ProviderTokenSet`` into canonical JSON bytes for AEAD encryption.

    Returns:
        UTF-8 encoded JSON bytes representing the token set.
    """
    payload = {
        "access_token": tokens.access_token.get_secret_value(),
        "token_type": tokens.token_type,
        "scopes": sorted(tokens.scopes),
        "expires_at": tokens.expires_at.isoformat(),
        "refresh_token": tokens.refresh_token.get_secret_value() if tokens.refresh_token is not None else None,
        "id_token": tokens.id_token.get_secret_value() if tokens.id_token is not None else None,
    }
    return json.dumps(payload).encode("utf-8")


def deserialize_oauth_tokens(raw: bytes) -> ProviderTokenSet:
    """Deserialize canonical JSON bytes back into a ``ProviderTokenSet``.

    Returns:
        Reconstructed ``ProviderTokenSet`` instance.
    """
    payload = json.loads(raw.decode("utf-8"))
    expires_at = payload.get("expires_at")
    return ProviderTokenSet(
        access_token=SecretStr(payload["access_token"]),
        token_type=payload["token_type"],
        scopes=frozenset(payload.get("scopes") or ()),
        expires_at=datetime.fromisoformat(expires_at) if expires_at else datetime.now(UTC),
        refresh_token=SecretStr(payload["refresh_token"]) if payload.get("refresh_token") else None,
        id_token=SecretStr(payload["id_token"]) if payload.get("id_token") else None,
    )


class SQLAlchemyOAuthTransactionStore:
    """``OAuthTransactionStore`` adapter keeping PKCE verifiers and nonces encrypted with AES-GCM."""

    __slots__ = ("_alchemy_config", "_protector")

    def __init__(
        self,
        alchemy_config: SQLAlchemyAsyncConfig,
        protector: OAuthTransactionProtector,
    ) -> None:
        """Initialize the OAuth transaction store with an AEAD protector."""
        self._alchemy_config = alchemy_config
        self._protector = protector

    async def create(self, transaction: OAuthTransaction) -> None:
        """Encrypt PKCE/nonce secrets and persist a single-use OAuth transaction."""
        protected_secrets = await self._protect_secrets(transaction)
        async with OAuthTransactionService.new(config=self._alchemy_config) as oauth_transactions:
            await oauth_transactions.record(transaction, protected_secrets=protected_secrets)
            await oauth_transactions.repository.session.commit()

    async def consume(
        self,
        *,
        state_digest: bytes,
        binding_digest: bytes,
        provider: str,
        now: datetime,
    ) -> OAuthTransaction | None:
        """Consume a matching unexpired OAuth transaction atomically without burning mismatched callbacks.

        Returns:
            Consumed ``OAuthTransaction`` with decrypted secrets, or ``None`` if unmatched or expired.
        """
        async with OAuthTransactionService.new(config=self._alchemy_config) as oauth_transactions:
            oauth_transaction = await oauth_transactions.redeem(
                state_digest,
                binding_digest=binding_digest,
                provider=provider,
                now=now,
            )
            await oauth_transactions.repository.session.commit()
            if oauth_transaction is None:
                return None
            pkce_verifier, nonce = await self._unprotect_secrets(oauth_transaction)
            return oauth_transactions.to_transaction(oauth_transaction, pkce_verifier=pkce_verifier, nonce=nonce)

    async def _protect_secrets(self, transaction: OAuthTransaction) -> ProtectedOAuthSecret:
        secrets = {
            "pkce_verifier": transaction.pkce_verifier.get_secret_value(),
            "nonce": transaction.nonce.get_secret_value() if transaction.nonce is not None else None,
        }
        return await self._protector.protect(
            json.dumps(secrets).encode("utf-8"),
            associated_data=self._transaction_aad(transaction.provider, transaction.state_digest.hex()),
        )

    async def _unprotect_secrets(self, oauth_transaction: m.OAuthTransaction) -> tuple[SecretStr, SecretStr | None]:
        serialized_secrets = await self._protector.unprotect(
            ProtectedOAuthSecret(
                ciphertext=oauth_transaction.protected_payload,
                key_version=oauth_transaction.key_version,
            ),
            associated_data=self._transaction_aad(oauth_transaction.provider, oauth_transaction.state_hash),
        )
        secrets = json.loads(serialized_secrets.decode("utf-8"))
        nonce = secrets.get("nonce")
        return SecretStr(secrets["pkce_verifier"]), SecretStr(nonce) if nonce else None

    @staticmethod
    def _transaction_aad(provider: str, state_hash: str) -> bytes:
        return f"oauth_tx|{provider}|{state_hash}".encode()


class SQLAlchemyOAuthAccountStore:
    """``OAuthAccountStore`` adapter persisting linked OAuth identities and encrypted provider tokens."""

    __slots__ = ("_alchemy_config", "_protector")

    def __init__(
        self,
        alchemy_config: SQLAlchemyAsyncConfig,
        protector: OAuthTransactionProtector,
    ) -> None:
        """Initialize the OAuth account store with an AEAD protector."""
        self._alchemy_config = alchemy_config
        self._protector = protector

    async def link(
        self,
        account_id: str,
        identity: ProviderIdentity,
        grant: ProviderGrant,
        tokens: ProviderTokenSet,
        *,
        retain_tokens: bool = False,
        now: datetime,
    ) -> LinkedProviderAccount:
        """Link an external OAuth identity to an existing user account.

        An identity that belongs to another user, or a provider the user already linked, surfaces as the
        ``AccountLinkError`` raised by ``OAuthAccountService.link``.

        Returns:
            Persisted ``LinkedProviderAccount`` record.

        Raises:
            OAuthAccountError: If ``account_id`` is not a valid UUID.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            raise OAuthAccountError
        protected_tokens = await self._protect_retained_tokens(identity, tokens, retain_tokens=retain_tokens)
        async with OAuthAccountService.new(config=self._alchemy_config) as oauth_accounts:
            oauth_account = await oauth_accounts.link(
                user_id,
                identity,
                grant=grant,
                protected_tokens=protected_tokens,
                now=now,
            )
            await oauth_accounts.repository.session.commit()
            return oauth_accounts.to_linked_account(oauth_account)

    async def login(
        self,
        identity: ProviderIdentity,
        grant: ProviderGrant,
        tokens: ProviderTokenSet,
        *,
        provision_unknown: bool,
        retain_tokens: bool,
        now: datetime,
    ) -> OAuthLoginOutcome:
        """Authenticate or optionally provision a user via an external OAuth identity.

        An unlinked identity that may not be provisioned, or whose email is already registered, surfaces as
        the ``AccountLinkError`` raised by ``OAuthServices.login``.

        Returns:
            ``OAuthLoginOutcome`` containing the linked account and provisioning flag.
        """
        protected_tokens = await self._protect_retained_tokens(identity, tokens, retain_tokens=retain_tokens)
        async with OAuthServices.new(config=self._alchemy_config) as services:
            outcome = await services.login(
                identity,
                grant=grant,
                protected_tokens=protected_tokens,
                provision_unknown=provision_unknown,
                now=now,
            )
            await services.session.commit()
            return outcome

    async def resolve_provider_account(self, account_id: str, provider: str) -> LinkedProviderAccount | None:
        """Resolve an account's linked OAuth identity for the named provider.

        Returns:
            Matching ``LinkedProviderAccount``, or ``None`` if not linked.
        """
        user_id = UserService.to_user_id(account_id)
        if user_id is None:
            return None
        async with OAuthAccountService.new(config=self._alchemy_config) as oauth_accounts:
            oauth_account = await oauth_accounts.get_one_or_none(user_id=user_id, oauth_name=provider)
            return oauth_accounts.to_linked_account(oauth_account) if oauth_account is not None else None

    async def upgrade(
        self,
        account_id: str,
        provider_account_id: str,
        identity: ProviderIdentity,
        grant: ProviderGrant,
        tokens: ProviderTokenSet,
        *,
        retain_tokens: bool,
        now: datetime,
    ) -> LinkedProviderAccount:
        """Upgrade scopes and optionally replace retained tokens on an existing OAuth link.

        Returns:
            Updated ``LinkedProviderAccount`` record.

        Raises:
            AccountLinkError: If identifiers are invalid or no matching linked account exists.
        """
        user_id = UserService.to_user_id(account_id)
        oauth_account_id = OAuthAccountService.to_oauth_account_id(provider_account_id)
        if user_id is None or oauth_account_id is None:
            raise AccountLinkError
        protected_tokens = await self._protect_retained_tokens(identity, tokens, retain_tokens=retain_tokens)
        async with OAuthAccountService.new(config=self._alchemy_config) as oauth_accounts:
            oauth_account = await oauth_accounts.find_owned(
                oauth_account_id,
                user_id=user_id,
                provider=identity.provider,
            )
            if oauth_account is None:
                raise AccountLinkError
            await oauth_accounts.replace_grant(
                oauth_account,
                grant=grant,
                protected_tokens=protected_tokens,
                now=now,
                advance_version=True,
            )
            await oauth_accounts.repository.session.commit()
            return oauth_accounts.to_linked_account(oauth_account)

    async def unlink(
        self,
        account_id: str,
        provider: str,
        provider_account_id: str,
        *,
        require_remaining: bool,
        now: datetime,
    ) -> UnlinkOutcome:
        """Atomically unlink an owned OAuth identity while protecting the user's final login method.

        Returns:
            ``UnlinkOutcome`` describing whether the link was removed, missing, or blocked as the final method.
        """
        del now
        user_id = UserService.to_user_id(account_id)
        oauth_account_id = OAuthAccountService.to_oauth_account_id(provider_account_id)
        if user_id is None or oauth_account_id is None:
            return UnlinkOutcome(UnlinkStatus.NOT_FOUND)
        async with OAuthServices.new(config=self._alchemy_config) as services:
            status = await services.unlink(user_id, oauth_account_id, provider, require_remaining=require_remaining)
            await services.session.commit()
        return UnlinkOutcome(status, provider_account_id if status is UnlinkStatus.UNLINKED else None)

    async def get_tokens(self, provider_account_id: str, *, now: datetime) -> StoredProviderTokens | None:
        """Decrypt and return retained OAuth tokens for a linked account.

        Returns:
            ``StoredProviderTokens`` with version metadata, or ``None`` if unavailable.
        """
        del now
        oauth_account_id = OAuthAccountService.to_oauth_account_id(provider_account_id)
        if oauth_account_id is None:
            return None
        async with OAuthAccountService.new(config=self._alchemy_config) as oauth_accounts:
            oauth_account = await oauth_accounts.get_one_or_none(id=oauth_account_id)
            if oauth_account is None:
                return None
            tokens = await self._unprotect_tokens(oauth_account)
            if tokens is None:
                return None
            return oauth_accounts.to_stored_tokens(oauth_account, tokens)

    async def replace_tokens(
        self,
        provider_account_id: str,
        *,
        expected_version: int,
        tokens: ProviderTokenSet,
        now: datetime,
    ) -> bool:
        """Optimistically replace encrypted provider tokens when version matches.

        Returns:
            ``True`` if tokens were replaced, ``False`` on missing row or version mismatch.
        """
        del now
        oauth_account_id = OAuthAccountService.to_oauth_account_id(provider_account_id)
        if oauth_account_id is None:
            return False
        async with OAuthAccountService.new(config=self._alchemy_config) as oauth_accounts:
            oauth_account = await oauth_accounts.get_one_or_none(id=oauth_account_id)
            if oauth_account is None:
                return False
            protected_tokens = await self._protect_tokens(oauth_account.oauth_name, oauth_account.account_id, tokens)
            replaced = await oauth_accounts.replace_tokens(
                oauth_account, expected_version=expected_version, tokens=tokens, protected_tokens=protected_tokens
            )
            await oauth_accounts.repository.session.commit()
            return replaced

    async def discard_tokens(self, provider_account_id: str, *, expected_version: int | None = None) -> bool:
        """Remove retained encrypted tokens for a linked OAuth account.

        Returns:
            ``True`` if tokens were cleared, ``False`` on missing row or version mismatch.
        """
        oauth_account_id = OAuthAccountService.to_oauth_account_id(provider_account_id)
        if oauth_account_id is None:
            return False
        async with OAuthAccountService.new(config=self._alchemy_config) as oauth_accounts:
            discarded = await oauth_accounts.discard_tokens(oauth_account_id, expected_version=expected_version)
            await oauth_accounts.repository.session.commit()
            return discarded

    async def stage_revocation_retry(
        self,
        failure: OAuthRevocationFailure,
        tokens: ProviderTokenSet,
        *,
        expected_version: int,
    ) -> bool:
        """Persist encrypted tokens for retry after an upstream revocation error.

        Returns:
            ``True`` if staged tokens were persisted, ``False`` on missing row or version mismatch.
        """
        return await self.replace_tokens(
            failure.provider_account_id,
            expected_version=expected_version,
            tokens=tokens,
            now=failure.occurred_at,
        )

    async def _protect_retained_tokens(
        self,
        identity: ProviderIdentity,
        tokens: ProviderTokenSet,
        *,
        retain_tokens: bool,
    ) -> ProtectedOAuthSecret | None:
        if not retain_tokens:
            return None
        return await self._protect_tokens(identity.provider, identity.subject, tokens)

    async def _protect_tokens(self, provider: str, subject: str, tokens: ProviderTokenSet) -> ProtectedOAuthSecret:
        return await self._protector.protect(
            serialize_oauth_tokens(tokens), associated_data=oauth_account_aad(provider, subject)
        )

    async def _unprotect_tokens(self, oauth_account: m.UserOAuthAccount) -> ProviderTokenSet | None:
        if oauth_account.protected_tokens is None or oauth_account.key_version is None:
            return None
        serialized_tokens = await self._protector.unprotect(
            ProtectedOAuthSecret(ciphertext=oauth_account.protected_tokens, key_version=oauth_account.key_version),
            associated_data=oauth_account_aad(oauth_account.oauth_name, oauth_account.account_id),
        )
        return deserialize_oauth_tokens(serialized_tokens)
