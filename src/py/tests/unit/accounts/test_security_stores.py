"""Unit and conformance tests for MFA, Passkeys, OAuth, and API key persistence adapters."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from advanced_alchemy.base import orm_registry
from litestar_security.accounts import MFALoginChallenge, SecretProtectorKey
from litestar_security.authentication import InvalidCredentials, VerificationUnavailable
from litestar_security.context import Principal
from litestar_security.providers.api_key import APIKeyClaims
from litestar_security.providers.oauth import (
    OAuthOperation,
    OAuthTransaction,
    OAuthTransactionProtectorKey,
    ProviderGrant,
    ProviderIdentity,
    ProviderTokenSet,
    SecretStr,
)
from litestar_security.testing import (
    assert_api_key_store_conformance,
    assert_mfa_login_challenge_store_conformance,
    assert_mfa_store_conformance,
    assert_oauth_account_store_conformance,
    assert_oauth_transaction_protector_conformance,
    assert_oauth_transaction_store_conformance,
    assert_passkey_store_conformance,
    assert_secret_protector_conformance,
    assert_step_up_store_conformance,
    assert_webauthn_challenge_store_conformance,
)
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.db import models as m
from app.domain.accounts.security import (
    APIKeyIdentityResolver,
    SQLAlchemyAPIKeyStore,
    SQLAlchemyMFALoginChallengeService,
    SQLAlchemyMFAService,
    SQLAlchemyOAuthAccountStore,
    SQLAlchemyOAuthTransactionStore,
    SQLAlchemyPasskeyStore,
    SQLAlchemyStepUpService,
    build_api_key_service,
    build_oauth_protector,
    build_secret_protector,
)
from app.lib.secrets import API_KEY_PEPPER_INFO, OAUTH_PROTECTOR_INFO, TOTP_PROTECTOR_INFO, derive_subkey
from app.lib.settings import AppSettings, DatabaseSettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio

DEFAULT_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _uuid_identifier(namespace: str, sequence: int) -> str:
    return str(uuid5(NAMESPACE_DNS, f"{namespace}:{sequence}"))


async def _make_sqlite_config(tmp_path: Path, name: str) -> SQLAlchemyAsyncConfig:
    db_file = tmp_path / f"{name}.sqlite3"
    cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{db_file}").get_config()
    async with cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)
    return cfg


async def _seed_conformance_users(cfg: SQLAlchemyAsyncConfig) -> None:
    async with cfg.get_session() as session:
        for ns in (
            "conformance-account",
            "conformance-principal",
            "conformance-session-other",
            "conformance-session-owner",
            "conformance-subject",
        ):
            uid = UUID(_uuid_identifier(ns, 0))
            if await session.scalar(select(m.User.id).where(m.User.id == uid)) is None:
                session.add(m.User(id=uid, email=f"{ns}@example.com", is_active=True, is_verified=True))
        await session.commit()


async def test_protectors_conformance_and_key_rotation() -> None:
    settings_v1 = Settings(app=AppSettings(SECRET_KEY="master-secret-v1"))
    settings_v2 = Settings(app=AppSettings(SECRET_KEY="master-secret-v2"))

    await assert_secret_protector_conformance(lambda: build_secret_protector(settings_v1))
    await assert_oauth_transaction_protector_conformance(lambda: build_oauth_protector(settings_v1))

    totp_v1 = build_secret_protector(settings_v1, key_version="v1")
    sealed_totp = await totp_v1.protect(b"totp-secret-bytes", associated_data=b"aad-totp")
    totp_v2 = build_secret_protector(
        settings_v2,
        key_version="v2",
        retained_keys=(SecretProtectorKey("v1", derive_subkey("master-secret-v1", TOTP_PROTECTOR_INFO)),),
    )
    assert await totp_v2.unprotect(sealed_totp, associated_data=b"aad-totp") == b"totp-secret-bytes"

    oauth_v1 = build_oauth_protector(settings_v1, key_version="v1")
    sealed_oauth = await oauth_v1.protect(b"oauth-pkce-verifier", associated_data=b"aad-oauth")
    oauth_v2 = build_oauth_protector(
        settings_v2,
        key_version="v2",
        retained_keys=(OAuthTransactionProtectorKey("v1", derive_subkey("master-secret-v1", OAUTH_PROTECTOR_INFO)),),
    )
    assert await oauth_v2.unprotect(sealed_oauth, associated_data=b"aad-oauth") == b"oauth-pkce-verifier"


async def test_mfa_step_up_passkey_oauth_and_api_key_store_conformance(tmp_path: Path) -> None:
    configs: list[SQLAlchemyAsyncConfig] = []

    async def prepare(prefix: str, count: int) -> list[SQLAlchemyAsyncConfig]:
        items: list[SQLAlchemyAsyncConfig] = []
        for idx in range(count):
            cfg = await _make_sqlite_config(tmp_path, f"{prefix}_{idx}")
            await _seed_conformance_users(cfg)
            configs.append(cfg)
            items.append(cfg)
        return items

    settings = Settings(app=AppSettings(SECRET_KEY="store-conformance-secret"))
    protector = build_oauth_protector(settings)

    try:
        api_cfgs = iter(await prepare("api_key", 2))
        await assert_api_key_store_conformance(
            lambda: SQLAlchemyAPIKeyStore(next(api_cfgs)),
            identifiers=_uuid_identifier,
        )

        mfa_cfgs = iter(await prepare("mfa", 2))
        await assert_mfa_store_conformance(
            lambda: SQLAlchemyMFAService(next(mfa_cfgs)),
            identifiers=_uuid_identifier,
        )

        mfa_login_cfgs = iter(await prepare("mfa_login", 2))
        await assert_mfa_login_challenge_store_conformance(
            lambda: SQLAlchemyMFALoginChallengeService(next(mfa_login_cfgs)),
            identifiers=_uuid_identifier,
        )

        step_up_cfgs = iter(await prepare("step_up", 6))
        await assert_step_up_store_conformance(
            lambda: SQLAlchemyStepUpService(next(step_up_cfgs)),
            identifiers=_uuid_identifier,
        )

        passkey_cfgs = iter(await prepare("passkey", 2))
        await assert_passkey_store_conformance(
            lambda: SQLAlchemyPasskeyStore(next(passkey_cfgs)),
            identifiers=_uuid_identifier,
        )

        webauthn_cfgs = iter(await prepare("webauthn", 2))
        await assert_webauthn_challenge_store_conformance(
            lambda: SQLAlchemyPasskeyStore(next(webauthn_cfgs)),
            identifiers=_uuid_identifier,
        )

        oauth_tx_cfgs = iter(await prepare("oauth_tx", 2))
        await assert_oauth_transaction_store_conformance(
            lambda: SQLAlchemyOAuthTransactionStore(next(oauth_tx_cfgs), protector),
        )

        oauth_acc_cfgs = iter(await prepare("oauth_acc", 2))
        await assert_oauth_account_store_conformance(
            lambda: SQLAlchemyOAuthAccountStore(next(oauth_acc_cfgs), protector),
            identifiers=_uuid_identifier,
        )
    finally:
        for cfg in configs:
            await cfg.get_engine().dispose()


async def test_mfa_login_challenge_atomic_burn_and_oauth_ciphertext(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "ciphertext_and_burn")
    settings = Settings(app=AppSettings(SECRET_KEY="ciphertext-check-secret"))
    protector = build_oauth_protector(settings)
    try:
        await _seed_conformance_users(cfg)
        account_id = _uuid_identifier("conformance-account", 0)

        challenge_store = SQLAlchemyMFALoginChallengeService(cfg)
        challenge = MFALoginChallenge(
            challenge_digest=b"c" * 32,
            account_id=account_id,
            security_epoch=1,
            client_key="127.0.0.1",
            issued_at=DEFAULT_NOW,
            expires_at=DEFAULT_NOW + timedelta(minutes=5),
        )
        await challenge_store.put(challenge)
        r1, r2 = await asyncio.gather(
            challenge_store.consume(b"c" * 32, account_id=account_id, security_epoch=1, now=DEFAULT_NOW),
            challenge_store.consume(b"c" * 32, account_id=account_id, security_epoch=1, now=DEFAULT_NOW),
        )
        assert sum(item is not None for item in (r1, r2)) == 1

        tx_store = SQLAlchemyOAuthTransactionStore(cfg, protector)
        raw_verifier = "pkce-verifier-plaintext-never-stored-raw-1234567890"
        tx = OAuthTransaction(
            state_digest=b"s" * 32,
            binding_digest=b"b" * 32,
            operation=OAuthOperation.LOGIN,
            provider="github",
            expected_issuer=None,
            redirect_uri="http://localhost:8000/api/auth/oauth/github/callback",
            return_to="/",
            requested_scopes=frozenset({"user:email"}),
            pkce_verifier=SecretStr(raw_verifier),
            expires_at=DEFAULT_NOW + timedelta(minutes=5),
        )
        await tx_store.create(tx)
        async with cfg.get_session() as session:
            tx_row = await session.scalar(select(m.OAuthTransaction))
            assert tx_row is not None
            assert raw_verifier.encode("utf-8") not in tx_row.protected_payload

        acc_store = SQLAlchemyOAuthAccountStore(cfg, protector)
        raw_token = "gho_plaintext_access_token_never_stored_raw"
        linked = await acc_store.link(
            account_id,
            ProviderIdentity(
                provider="github",
                issuer="https://github.com",
                subject="gh-user-1",
                display_name="Octocat",
                email="octo@example.com",
                email_verified=True,
                raw_claims={"id": 1},
            ),
            ProviderGrant(scopes=frozenset({"user:email"}), expires_at=DEFAULT_NOW + timedelta(hours=1)),
            ProviderTokenSet(
                access_token=SecretStr(raw_token),
                token_type="Bearer",
                scopes=frozenset({"user:email"}),
                expires_at=DEFAULT_NOW + timedelta(hours=1),
            ),
            retain_tokens=True,
            now=DEFAULT_NOW,
        )
        async with cfg.get_session() as session:
            acc_row = await session.scalar(select(m.UserOAuthAccount))
            assert acc_row is not None
            assert acc_row.protected_tokens is not None
            assert raw_token.encode("utf-8") not in acc_row.protected_tokens

        stored = await acc_store.get_tokens(linked.provider_account_id, now=DEFAULT_NOW)
        assert stored is not None
        assert stored.tokens.access_token.get_secret_value() == raw_token
    finally:
        await cfg.get_engine().dispose()


async def test_api_key_service_and_identity_resolver(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "api_key_resolver")
    try:
        async with cfg.get_session() as session:
            role = m.Role(name="User", slug="user")
            team = m.Team(name="Platform", slug="platform")
            active_user = m.User(email="active@example.com", name="Active", is_active=True, is_verified=True)
            inactive_user = m.User(email="inactive@example.com", name="Inactive", is_active=False, is_verified=True)
            session.add_all([role, team, active_user, inactive_user])
            await session.flush()
            session.add(m.UserRole(user_id=active_user.id, role_id=role.id, assigned_at=DEFAULT_NOW))
            session.add(m.TeamMember(user_id=active_user.id, team_id=team.id, role=m.TeamRoles.MEMBER))
            await session.commit()
            active_id = str(active_user.id)
            inactive_id = str(inactive_user.id)

        store = SQLAlchemyAPIKeyStore(cfg)
        pepper = derive_subkey("api-key-test-secret", API_KEY_PEPPER_INFO)
        service = build_api_key_service(store, pepper)
        issued = await service.issue(subject_id=active_id)
        async with cfg.get_session() as session:
            key_row = await session.scalar(select(m.APIKey).where(m.APIKey.key_id == issued.key_id))
            assert key_row is not None
            assert issued.value != key_row.key_hash

        resolver = APIKeyIdentityResolver(cfg)
        principal = await resolver.resolve(APIKeyClaims(key_id=issued.key_id, subject_id=active_id))
        assert isinstance(principal, Principal)
        assert principal.user is not None
        unloaded = sa_inspect(principal.user).unloaded
        assert "roles" not in unloaded
        assert "teams" not in unloaded

        inactive_res = await resolver.resolve(APIKeyClaims(key_id="k2", subject_id=inactive_id))
        assert isinstance(inactive_res, InvalidCredentials)

        class _BrokenConfig:
            def get_session(self) -> object:
                stmt = "SELECT 1"
                cause = RuntimeError()
                raise OperationalError(stmt, {}, cause)

        broken_resolver = APIKeyIdentityResolver(_BrokenConfig())  # type: ignore[arg-type]
        outage_res = await broken_resolver.resolve(APIKeyClaims(key_id="k3", subject_id=active_id))
        assert isinstance(outage_res, VerificationUnavailable)
    finally:
        await cfg.get_engine().dispose()
