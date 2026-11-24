"""SQLAlchemy persistence adapters for ``litestar-security`` OAuth transactions and linked accounts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hmac import compare_digest
from typing import TYPE_CHECKING, Any
from uuid import UUID

from anyio import Lock
from litestar_security.providers.oauth import (
    AccountLinkError,
    AESGCMOAuthTransactionProtector,
    LinkedProviderAccount,
    OAuthAccountError,
    OAuthLoginOutcome,
    OAuthOperation,
    OAuthRevocationFailure,
    OAuthTransaction,
    OAuthTransactionProtector,
    OAuthTransactionProtectorKey,
    ProtectedOAuthSecret,
    ProviderGrant,
    ProviderIdentity,
    ProviderTokenReference,
    ProviderTokenSet,
    SecretStr,
    StoredProviderTokens,
    UnlinkOutcome,
    UnlinkStatus,
)
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import undefer_group

from app.db import models as m
from app.lib.constants import DEFAULT_ACCESS_ROLE
from app.lib.secrets import OAUTH_PROTECTOR_INFO, derive_subkey

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

    from app.lib.settings import Settings

__all__ = (
    "SQLAlchemyOAuthAccountStore",
    "SQLAlchemyOAuthTransactionStore",
    "build_oauth_protector",
)


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


def build_oauth_protector(
    settings: Settings,
    *,
    key_version: str = "v1",
    retained_keys: Sequence[OAuthTransactionProtectorKey] = (),
) -> AESGCMOAuthTransactionProtector:
    """Build an ``AESGCMOAuthTransactionProtector`` using an HKDF-derived 32-byte key."""
    active = OAuthTransactionProtectorKey(
        key_version=key_version,
        key=derive_subkey(settings.app.SECRET_KEY, OAUTH_PROTECTOR_INFO),
    )
    return AESGCMOAuthTransactionProtector(active_key=active, retained_keys=tuple(retained_keys))


def _serialize_tokens(tokens: ProviderTokenSet) -> bytes:
    payload: dict[str, Any] = {
        "access_token": tokens.access_token.get_secret_value(),
        "token_type": tokens.token_type,
        "scopes": sorted(tokens.scopes),
        "expires_at": _ensure_utc(tokens.expires_at).isoformat(),
        "refresh_token": tokens.refresh_token.get_secret_value() if tokens.refresh_token is not None else None,
        "id_token": tokens.id_token.get_secret_value() if tokens.id_token is not None else None,
    }
    return json.dumps(payload).encode("utf-8")


def _deserialize_tokens(raw: bytes) -> ProviderTokenSet:
    data = json.loads(raw.decode("utf-8"))
    expires_raw = data.get("expires_at")
    return ProviderTokenSet(
        access_token=SecretStr(data["access_token"]),
        token_type=data["token_type"],
        scopes=frozenset(data.get("scopes") or ()),
        expires_at=_ensure_utc(datetime.fromisoformat(expires_raw)) if expires_raw else datetime.now(UTC),
        refresh_token=SecretStr(data["refresh_token"]) if data.get("refresh_token") else None,
        id_token=SecretStr(data["id_token"]) if data.get("id_token") else None,
    )


def _row_to_linked_account(row: m.UserOAuthAccount) -> LinkedProviderAccount:
    return LinkedProviderAccount(
        provider_account_id=str(row.id),
        account_id=str(row.user_id),
        provider=row.oauth_name,
        issuer=row.issuer or "",
        subject=row.account_id,
        grant=ProviderGrant(
            scopes=frozenset(row.scopes or ()),
            expires_at=_ensure_utc(row.token_expires_at) if row.token_expires_at is not None else _ensure_utc(row.created_at),
        ),
        linked_at=_ensure_utc(row.created_at),
    )


class SQLAlchemyOAuthTransactionStore:
    """SQLAlchemy ``OAuthTransactionStore`` encrypting PKCE verifiers and nonces with AES-GCM."""

    __slots__ = ("_alchemy_config", "_lock", "_protector")

    def __init__(
        self,
        alchemy_config: SQLAlchemyAsyncConfig,
        protector: OAuthTransactionProtector,
    ) -> None:
        """Initialize the OAuth transaction store with an AEAD protector."""
        self._alchemy_config = alchemy_config
        self._protector = protector
        self._lock = Lock()

    async def create(self, transaction: OAuthTransaction) -> None:
        """Encrypt PKCE/nonce secrets and persist a single-use OAuth transaction."""
        state_hex = transaction.state_digest.hex()
        aad = f"oauth_tx|{transaction.provider}|{state_hex}".encode()
        secret_payload = json.dumps(
            {
                "pkce_verifier": transaction.pkce_verifier.get_secret_value(),
                "nonce": transaction.nonce.get_secret_value() if transaction.nonce is not None else None,
            }
        ).encode("utf-8")
        protected = await self._protector.protect(secret_payload, associated_data=aad)
        row = m.OAuthTransaction(
            state_hash=state_hex,
            binding_digest=transaction.binding_digest.hex(),
            operation=transaction.operation.value,
            provider=transaction.provider,
            expected_issuer=transaction.expected_issuer,
            redirect_uri=transaction.redirect_uri,
            return_to=transaction.return_to,
            requested_scopes=sorted(transaction.requested_scopes),
            protected_payload=protected.ciphertext,
            key_version=protected.key_version,
            user_id=_parse_uuid(transaction.account_id),
            session_binding=transaction.session_binding,
            security_epoch=transaction.security_epoch,
            provider_account_id=transaction.provider_account_id,
            step_up_purpose=transaction.step_up_purpose,
            maximum_authentication_age=transaction.maximum_authentication_age,
            expires_at=_ensure_utc(transaction.expires_at),
        )
        async with self._lock, self._alchemy_config.get_session() as session:
            session.add(row)
            await session.commit()

    async def consume(
        self,
        *,
        state_digest: bytes,
        binding_digest: bytes,
        provider: str,
        now: datetime,
    ) -> OAuthTransaction | None:
        """Consume a matching unexpired OAuth transaction atomically without burning mismatched callbacks."""
        now_utc = _ensure_utc(now)
        state_hex = state_digest.hex()
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.OAuthTransaction).where(
                    m.OAuthTransaction.state_hash == state_hex,
                    m.OAuthTransaction.consumed_at.is_(None),
                )
            )
            if row is None:
                return None
            if row.provider != provider or not compare_digest(bytes.fromhex(row.binding_digest), binding_digest):
                return None
            if _ensure_utc(row.expires_at) <= now_utc:
                return None
            burn = await session.execute(
                update(m.OAuthTransaction)
                .where(
                    m.OAuthTransaction.id == row.id,
                    m.OAuthTransaction.consumed_at.is_(None),
                )
                .values(consumed_at=now_utc)
            )
            await session.commit()
            if int(getattr(burn, "rowcount", 0) or 0) != 1:
                return None

        aad = f"oauth_tx|{row.provider}|{row.state_hash}".encode()
        raw = await self._protector.unprotect(
            ProtectedOAuthSecret(ciphertext=row.protected_payload, key_version=row.key_version),
            associated_data=aad,
        )
        secret_data = json.loads(raw.decode("utf-8"))
        return OAuthTransaction(
            state_digest=bytes.fromhex(row.state_hash),
            binding_digest=bytes.fromhex(row.binding_digest),
            operation=OAuthOperation(row.operation),
            provider=row.provider,
            expected_issuer=row.expected_issuer,
            redirect_uri=row.redirect_uri,
            return_to=row.return_to or "/",
            requested_scopes=frozenset(row.requested_scopes),
            pkce_verifier=SecretStr(secret_data["pkce_verifier"]),
            nonce=SecretStr(secret_data["nonce"]) if secret_data.get("nonce") else None,
            account_id=str(row.user_id) if row.user_id is not None else None,
            session_binding=row.session_binding,
            security_epoch=row.security_epoch,
            provider_account_id=row.provider_account_id,
            step_up_purpose=row.step_up_purpose,
            maximum_authentication_age=row.maximum_authentication_age,
            expires_at=_ensure_utc(row.expires_at),
        )


class SQLAlchemyOAuthAccountStore:
    """SQLAlchemy ``OAuthAccountStore`` persisting linked OAuth identities and encrypted provider tokens."""

    __slots__ = ("_alchemy_config", "_lock", "_protector")

    def __init__(
        self,
        alchemy_config: SQLAlchemyAsyncConfig,
        protector: OAuthTransactionProtector,
    ) -> None:
        """Initialize the OAuth account store with an AEAD protector."""
        self._alchemy_config = alchemy_config
        self._protector = protector
        self._lock = Lock()

    async def _protect_tokens(
        self,
        provider: str,
        subject: str,
        tokens: ProviderTokenSet,
    ) -> ProtectedOAuthSecret:
        aad = f"oauth_account|{provider}|{subject}".encode()
        return await self._protector.protect(_serialize_tokens(tokens), associated_data=aad)

    async def _unprotect_tokens(
        self,
        row: m.UserOAuthAccount,
    ) -> ProviderTokenSet | None:
        if row.protected_tokens is None or row.key_version is None:
            return None
        aad = f"oauth_account|{row.oauth_name}|{row.account_id}".encode()
        raw = await self._protector.unprotect(
            ProtectedOAuthSecret(ciphertext=row.protected_tokens, key_version=row.key_version),
            associated_data=aad,
        )
        return _deserialize_tokens(raw)

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
        """Link an external OAuth identity to an existing user account."""
        uid = _parse_uuid(account_id)
        if uid is None:
            raise OAuthAccountError
        now_utc = _ensure_utc(now)
        protected = await self._protect_tokens(identity.provider, identity.subject, tokens) if retain_tokens else None
        async with self._lock, self._alchemy_config.get_session() as session:
            existing_identity = await session.scalar(
                select(m.UserOAuthAccount).where(
                    m.UserOAuthAccount.oauth_name == identity.provider,
                    m.UserOAuthAccount.account_id == identity.subject,
                )
            )
            if existing_identity is not None:
                if existing_identity.user_id != uid:
                    raise AccountLinkError
                existing_identity.issuer = identity.issuer
                existing_identity.scopes = sorted(grant.scopes)
                existing_identity.token_expires_at = _ensure_utc(grant.expires_at)
                existing_identity.protected_tokens = protected.ciphertext if protected is not None else None
                existing_identity.key_version = protected.key_version if protected is not None else None
                existing_identity.token_version += 1
                existing_identity.last_login_at = now_utc
                await session.commit()
                return _row_to_linked_account(existing_identity)

            same_provider = await session.scalar(
                select(m.UserOAuthAccount.id).where(
                    m.UserOAuthAccount.user_id == uid,
                    m.UserOAuthAccount.oauth_name == identity.provider,
                )
            )
            if same_provider is not None:
                raise AccountLinkError

            row = m.UserOAuthAccount(
                user_id=uid,
                oauth_name=identity.provider,
                issuer=identity.issuer,
                account_id=identity.subject,
                account_email=identity.email or "",
                protected_tokens=protected.ciphertext if protected is not None else None,
                key_version=protected.key_version if protected is not None else None,
                token_version=1,
                scopes=sorted(grant.scopes),
                token_expires_at=_ensure_utc(grant.expires_at),
                provider_user_data=dict(identity.raw_claims) if identity.raw_claims else None,
                last_login_at=now_utc,
                created_at=now_utc,
                updated_at=now_utc,
            )
            session.add(row)
            await session.commit()
            return _row_to_linked_account(row)

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
        """Authenticate or optionally provision a user via an external OAuth identity."""
        now_utc = _ensure_utc(now)
        protected = await self._protect_tokens(identity.provider, identity.subject, tokens) if retain_tokens else None
        async with self._lock, self._alchemy_config.get_session() as session:
            existing = await session.scalar(
                select(m.UserOAuthAccount).where(
                    m.UserOAuthAccount.oauth_name == identity.provider,
                    m.UserOAuthAccount.account_id == identity.subject,
                )
            )
            if existing is not None:
                existing.scopes = sorted(grant.scopes)
                existing.token_expires_at = _ensure_utc(grant.expires_at)
                existing.protected_tokens = protected.ciphertext if protected is not None else None
                existing.key_version = protected.key_version if protected is not None else None
                existing.last_login_at = now_utc
                await session.commit()
                return OAuthLoginOutcome(linked=_row_to_linked_account(existing), provisioned=False)

            if not provision_unknown:
                raise AccountLinkError

            user = m.User(
                email=identity.email or f"{identity.provider}-{identity.subject}@oauth.local",
                name=identity.display_name,
                is_active=True,
                is_verified=bool(identity.email_verified),
                verified_at=now_utc.date() if identity.email_verified else None,
                security_epoch=1,
            )
            session.add(user)
            try:
                await session.flush()
            except IntegrityError as exc:
                await session.rollback()
                raise AccountLinkError from exc

            default_role = await session.scalar(select(m.Role).where(m.Role.name == DEFAULT_ACCESS_ROLE))
            if default_role is not None:
                session.add(m.UserRole(user_id=user.id, role_id=default_role.id, assigned_at=now_utc))

            row = m.UserOAuthAccount(
                user_id=user.id,
                oauth_name=identity.provider,
                issuer=identity.issuer,
                account_id=identity.subject,
                account_email=user.email,
                protected_tokens=protected.ciphertext if protected is not None else None,
                key_version=protected.key_version if protected is not None else None,
                token_version=1,
                scopes=sorted(grant.scopes),
                token_expires_at=_ensure_utc(grant.expires_at),
                provider_user_data=dict(identity.raw_claims) if identity.raw_claims else None,
                last_login_at=now_utc,
                created_at=now_utc,
                updated_at=now_utc,
            )
            session.add(row)
            await session.commit()
            return OAuthLoginOutcome(linked=_row_to_linked_account(row), provisioned=True)

    async def resolve_provider_account(self, account_id: str, provider: str) -> LinkedProviderAccount | None:
        """Resolve an account's linked OAuth identity for the named provider."""
        uid = _parse_uuid(account_id)
        if uid is None:
            return None
        async with self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserOAuthAccount).where(
                    m.UserOAuthAccount.user_id == uid,
                    m.UserOAuthAccount.oauth_name == provider,
                )
            )
            return _row_to_linked_account(row) if row is not None else None

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
        """Upgrade scopes and optionally replace retained tokens on an existing OAuth link."""
        uid = _parse_uuid(account_id)
        pid = _parse_uuid(provider_account_id)
        if uid is None or pid is None:
            raise AccountLinkError
        now_utc = _ensure_utc(now)
        protected = await self._protect_tokens(identity.provider, identity.subject, tokens) if retain_tokens else None
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserOAuthAccount).where(
                    m.UserOAuthAccount.id == pid,
                    m.UserOAuthAccount.user_id == uid,
                    m.UserOAuthAccount.oauth_name == identity.provider,
                )
            )
            if row is None:
                raise AccountLinkError
            row.scopes = sorted(grant.scopes)
            row.token_expires_at = _ensure_utc(grant.expires_at)
            row.protected_tokens = protected.ciphertext if protected is not None else None
            row.key_version = protected.key_version if protected is not None else None
            row.token_version += 1
            row.last_login_at = now_utc
            await session.commit()
            return _row_to_linked_account(row)

    async def unlink(
        self,
        account_id: str,
        provider: str,
        provider_account_id: str,
        *,
        require_remaining: bool,
        now: datetime,
    ) -> UnlinkOutcome:
        """Atomically unlink an owned OAuth identity while protecting the user's final login method."""
        del now
        uid = _parse_uuid(account_id)
        pid = _parse_uuid(provider_account_id)
        if uid is None or pid is None:
            return UnlinkOutcome(UnlinkStatus.NOT_FOUND)
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(
                select(m.UserOAuthAccount).where(
                    m.UserOAuthAccount.id == pid,
                    m.UserOAuthAccount.user_id == uid,
                    m.UserOAuthAccount.oauth_name == provider,
                )
            )
            if row is None:
                return UnlinkOutcome(UnlinkStatus.NOT_FOUND)
            if require_remaining:
                user = await session.scalar(
                    select(m.User).where(m.User.id == uid).options(undefer_group("security_sensitive"))
                )
                oauth_count = int(
                    (
                        await session.scalar(
                            select(func.count()).select_from(m.UserOAuthAccount).where(m.UserOAuthAccount.user_id == uid)
                        )
                    )
                    or 0
                )
                passkey_count = int(
                    (
                        await session.scalar(
                            select(func.count()).select_from(m.UserPasskey).where(m.UserPasskey.user_id == uid)
                        )
                    )
                    or 0
                )
                has_password = 1 if (user is not None and user.hashed_password is not None) else 0
                if oauth_count + passkey_count + has_password <= 1:
                    return UnlinkOutcome(UnlinkStatus.FINAL_METHOD)
            result = await session.execute(delete(m.UserOAuthAccount).where(m.UserOAuthAccount.id == row.id))
            await session.commit()
            if int(getattr(result, "rowcount", 0) or 0) != 1:
                return UnlinkOutcome(UnlinkStatus.NOT_FOUND)
            return UnlinkOutcome(UnlinkStatus.UNLINKED, provider_account_id)

    async def get_tokens(self, provider_account_id: str, *, now: datetime) -> StoredProviderTokens | None:
        """Decrypt and return retained OAuth tokens for a linked account."""
        del now
        pid = _parse_uuid(provider_account_id)
        if pid is None:
            return None
        async with self._alchemy_config.get_session() as session:
            row = await session.scalar(select(m.UserOAuthAccount).where(m.UserOAuthAccount.id == pid))
            if row is None:
                return None
            tokens = await self._unprotect_tokens(row)
            if tokens is None:
                return None
            reference = ProviderTokenReference(
                provider_account_id=str(row.id),
                version=row.token_version,
                scopes=frozenset(row.scopes or ()),
                expires_at=(
                    _ensure_utc(row.token_expires_at)
                    if row.token_expires_at is not None
                    else _ensure_utc(tokens.expires_at)
                ),
            )
            return StoredProviderTokens(reference=reference, tokens=tokens)

    async def replace_tokens(
        self,
        provider_account_id: str,
        *,
        expected_version: int,
        tokens: ProviderTokenSet,
        now: datetime,
    ) -> bool:
        """Optimistically replace encrypted provider tokens when version matches."""
        del now
        pid = _parse_uuid(provider_account_id)
        if pid is None:
            return False
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(select(m.UserOAuthAccount).where(m.UserOAuthAccount.id == pid))
            if row is None:
                return False
            protected = await self._protect_tokens(row.oauth_name, row.account_id, tokens)
            result = await session.execute(
                update(m.UserOAuthAccount)
                .where(
                    m.UserOAuthAccount.id == pid,
                    m.UserOAuthAccount.token_version == expected_version,
                )
                .values(
                    protected_tokens=protected.ciphertext,
                    key_version=protected.key_version,
                    token_version=expected_version + 1,
                    scopes=sorted(tokens.scopes),
                    token_expires_at=_ensure_utc(tokens.expires_at),
                )
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0) == 1

    async def discard_tokens(self, provider_account_id: str, *, expected_version: int | None = None) -> bool:
        """Remove retained encrypted tokens for a linked OAuth account."""
        pid = _parse_uuid(provider_account_id)
        if pid is None:
            return False
        async with self._lock, self._alchemy_config.get_session() as session:
            stmt = update(m.UserOAuthAccount).where(m.UserOAuthAccount.id == pid)
            if expected_version is not None:
                stmt = stmt.where(m.UserOAuthAccount.token_version == expected_version)
            result = await session.execute(
                stmt.values(
                    protected_tokens=None,
                    key_version=None,
                    token_version=m.UserOAuthAccount.token_version + 1,
                )
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0) == 1

    async def stage_revocation_retry(
        self,
        failure: OAuthRevocationFailure,
        tokens: ProviderTokenSet,
        *,
        expected_version: int,
    ) -> bool:
        """Persist encrypted tokens for retry after an upstream revocation error."""
        return await self.replace_tokens(
            failure.provider_account_id,
            expected_version=expected_version,
            tokens=tokens,
            now=failure.occurred_at,
        )
