"""PostgreSQL conformance and concurrency tests for the ``litestar-security`` persistence adapters."""

from __future__ import annotations

import asyncio
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from litestar_security.accounts import (
    LoginMethod,
    RateLimitPolicy,
    RecoveryCodeDigest,
    RevokeLoginMethodStatus,
    SecurityEvent,
)
from litestar_security.providers.api_key import APIKeyState
from litestar_security.providers.oauth import (
    AccountLinkError,
    ProviderGrant,
    ProviderIdentity,
    ProviderTokenSet,
    SecretStr,
    UnlinkStatus,
)
from litestar_security.testing import (
    StoreConformanceFactories,
    assert_api_key_store_conformance,
    assert_rate_limiter_conformance,
    assert_security_backend_conformance,
    assert_session_registry_conformance,
)
from sqlalchemy import func, select

from app.db import models as m
from app.domain.accounts.security import (
    SQLAlchemyAPIKeyStore,
    SQLAlchemyMFALoginChallengeService,
    SQLAlchemyMFAService,
    SQLAlchemyOAuthAccountStore,
    SQLAlchemyOAuthTransactionStore,
    SQLAlchemyPasskeyStore,
    SQLAlchemySecurityBackend,
    SQLAlchemyStepUpService,
    build_oauth_protector,
    build_rate_limiter,
)
from app.domain.accounts.services import RoleService
from app.lib.constants import DEFAULT_ACCESS_ROLE
from app.lib.settings import AppSettings, DatabaseSettings, Settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from litestar_security.providers.oauth import AESGCMOAuthTransactionProtector
    from pytest_databases.docker.postgres import PostgresService
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.security]

NOW = datetime(2026, 1, 1, tzinfo=UTC)
CONFORMANCE_ACCOUNTS = (
    "conformance-account",
    "conformance-principal",
    "conformance-session-other",
    "conformance-session-owner",
    "conformance-subject",
)
CONTENDERS = 6


def _account_id(namespace: str, sequence: int) -> str:
    return str(uuid5(NAMESPACE_DNS, f"{namespace}:{sequence}"))


def _event(operation: str) -> SecurityEvent:
    return SecurityEvent(event_id=f"evt-{operation}", occurred_at=NOW, operation=operation, outcome="success")


def _identity(provider: str, subject: str, *, email: str | None = None) -> ProviderIdentity:
    return ProviderIdentity(
        provider=provider,
        issuer=f"https://{provider}.example.com",
        subject=subject,
        display_name="Octocat",
        email=email,
        email_verified=email is not None,
        raw_claims={},
    )


def _grant() -> ProviderGrant:
    return ProviderGrant(scopes=frozenset({"user:email"}), expires_at=NOW + timedelta(hours=1))


def _tokens() -> ProviderTokenSet:
    return ProviderTokenSet(
        access_token=SecretStr("access-token"),
        token_type="Bearer",
        scopes=frozenset({"user:email"}),
        expires_at=NOW + timedelta(hours=1),
    )


def _api_key(key_id: str, subject_id: str) -> APIKeyState:
    return APIKeyState(key_id=key_id, subject_id=subject_id, digest=b"d" * 32)


@pytest.fixture
def oauth_protector() -> AESGCMOAuthTransactionProtector:
    return build_oauth_protector(Settings(app=AppSettings(SECRET_KEY="postgres-store-secret")))


@pytest.fixture
async def alchemy_config(engine: AsyncEngine, db_cleanup: None) -> AsyncIterator[SQLAlchemyAsyncConfig]:
    """Pooled Advanced Alchemy configuration on the worker database, so concurrent callers hold separate connections."""
    _ = db_cleanup
    pooled_config = DatabaseSettings(URL=engine.url.render_as_string(hide_password=False)).get_config()
    yield pooled_config
    await pooled_config.get_engine().dispose()


@pytest.fixture
async def account_id(sessionmaker: async_sessionmaker[AsyncSession], db_cleanup: None) -> str:
    """Account without a password, so the login methods a test adds are the only ones it has."""
    _ = db_cleanup
    async with sessionmaker() as db_session:
        user = m.User(email="passwordless@example.com", is_active=True, is_verified=True)
        db_session.add(user)
        await db_session.commit()
        return str(user.id)


@pytest.fixture
async def default_access_role(sessionmaker: async_sessionmaker[AsyncSession], db_cleanup: None) -> None:
    """Seed the default access role the way deployments do, so provisioning finds it instead of creating it."""
    _ = db_cleanup
    async with sessionmaker() as db_session:
        await RoleService(session=db_session).create({"name": DEFAULT_ACCESS_ROLE})
        await db_session.commit()


@pytest.fixture
async def isolated_alchemy_config(
    postgres_service: PostgresService,
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_cleanup: None,
) -> AsyncIterator[Callable[[], SQLAlchemyAsyncConfig]]:
    """Hand out configurations that each own a private clone of the worker database.

    The conformance suites require every store a factory returns to start from isolated state. Each clone
    already holds the accounts the suites reference, because foreign keys are enforced here.
    """
    _ = db_cleanup
    async with sessionmaker() as db_session:
        for namespace in CONFORMANCE_ACCOUNTS:
            user_id = UUID(_account_id(namespace, 0))
            db_session.add(m.User(id=user_id, email=f"{namespace}@example.com", is_active=True, is_verified=True))
        await db_session.commit()

    clones: dict[str, SQLAlchemyAsyncConfig] = {}

    def clone_worker_database() -> SQLAlchemyAsyncConfig:
        database = f"{postgres_service.database}_clone_{len(clones)}"
        postgres_service.drop_database_force(database)
        postgres_service.clone_template_database(database)
        url = engine.url.set(database=database).render_as_string(hide_password=False)
        clones[database] = DatabaseSettings(URL=url).get_config()
        return clones[database]

    yield clone_worker_database
    for database, cloned_config in clones.items():
        await cloned_config.get_engine().dispose()
        postgres_service.drop_database_force(database)


async def test_stores_pass_the_library_conformance_suites(
    isolated_alchemy_config: Callable[[], SQLAlchemyAsyncConfig],
    oauth_protector: AESGCMOAuthTransactionProtector,
) -> None:
    def backend() -> SQLAlchemySecurityBackend:
        return SQLAlchemySecurityBackend(isolated_alchemy_config(), clock=lambda: NOW)

    await assert_security_backend_conformance(
        StoreConformanceFactories(
            local_account_store=cast("Any", backend),
            session_registry=backend,
            mfa_store=lambda: SQLAlchemyMFAService(isolated_alchemy_config()),
            mfa_login_challenge_store=lambda: SQLAlchemyMFALoginChallengeService(isolated_alchemy_config()),
            step_up_store=lambda: SQLAlchemyStepUpService(isolated_alchemy_config()),
            passkey_store=lambda: SQLAlchemyPasskeyStore(isolated_alchemy_config()),
            webauthn_challenge_store=lambda: SQLAlchemyPasskeyStore(isolated_alchemy_config()),
            oauth_transaction_store=lambda: SQLAlchemyOAuthTransactionStore(isolated_alchemy_config(), oauth_protector),
            oauth_account_store=lambda: SQLAlchemyOAuthAccountStore(isolated_alchemy_config(), oauth_protector),
        ),
        identifiers=_account_id,
    )
    await assert_session_registry_conformance(backend, now=NOW, identifiers=_account_id)
    await assert_api_key_store_conformance(
        lambda: SQLAlchemyAPIKeyStore(isolated_alchemy_config()),
        identifiers=_account_id,
    )


async def test_rate_limiter_passes_the_library_conformance_suite(alchemy_config: SQLAlchemyAsyncConfig) -> None:
    await assert_rate_limiter_conformance(
        lambda limit: build_rate_limiter(
            alchemy_config,
            policies={"conformance.rate_limit": RateLimitPolicy(limit=limit, window=timedelta(seconds=60))},
            clock=lambda: NOW,
        ),
        limit=5,
        concurrency=20,
    )


async def test_concurrent_recovery_code_replacements_leave_exactly_one_set(
    alchemy_config: SQLAlchemyAsyncConfig,
    account_id: str,
) -> None:
    store = SQLAlchemyMFAService(alchemy_config)
    replacements = [
        tuple(
            RecoveryCodeDigest(account_id=account_id, pepper_version="v1", digest=bytes([contender, code]) * 16)
            for code in range(3)
        )
        for contender in range(CONTENDERS)
    ]

    for _ in range(3):
        await asyncio.gather(*(store.replace_recovery_codes(account_id, codes, now=NOW) for codes in replacements))

        async with alchemy_config.get_session() as db_session:
            stored_digests = set(await db_session.scalars(select(m.UserMFARecoveryCode.digest)))
        assert stored_digests in [{code.digest.hex() for code in codes} for codes in replacements]


async def test_concurrent_login_method_revocations_always_leave_one(
    alchemy_config: SQLAlchemyAsyncConfig,
    account_id: str,
) -> None:
    backend = SQLAlchemySecurityBackend(alchemy_config, clock=lambda: NOW)
    method_ids = [f"totp-{contender}" for contender in range(CONTENDERS)]
    for method_id in method_ids:
        await backend.register_login_method(
            account_id,
            LoginMethod(method_id, "totp", NOW),
            event=_event("login_method.register"),
        )

    outcomes = await asyncio.gather(
        *(
            backend.revoke_login_method(account_id, method_id, event=_event("login_method.revoke"))
            for method_id in method_ids
        )
    )

    assert Counter(outcome.status for outcome in outcomes) == {
        RevokeLoginMethodStatus.REVOKED: CONTENDERS - 1,
        RevokeLoginMethodStatus.FINAL_METHOD: 1,
    }
    assert len(await backend.list_methods(account_id)) == 1


async def test_a_totp_factor_does_not_let_the_last_provider_be_unlinked(
    alchemy_config: SQLAlchemyAsyncConfig,
    oauth_protector: AESGCMOAuthTransactionProtector,
    account_id: str,
) -> None:
    backend = SQLAlchemySecurityBackend(alchemy_config, clock=lambda: NOW)
    store = SQLAlchemyOAuthAccountStore(alchemy_config, oauth_protector)
    link = await store.link(account_id, _identity("github", "github-subject"), _grant(), _tokens(), now=NOW)
    await backend.register_login_method(
        account_id,
        LoginMethod("totp-1", "totp", NOW),
        event=_event("login_method.register"),
    )

    unlinked = await store.unlink(account_id, link.provider, link.provider_account_id, require_remaining=True, now=NOW)
    revoked = await backend.revoke_login_method(account_id, "totp-1", event=_event("login_method.revoke"))

    assert unlinked.status is UnlinkStatus.FINAL_METHOD
    assert revoked.status is RevokeLoginMethodStatus.REVOKED


async def test_concurrent_unlinks_remove_one_link_and_tell_each_loser_why(
    alchemy_config: SQLAlchemyAsyncConfig,
    oauth_protector: AESGCMOAuthTransactionProtector,
    account_id: str,
) -> None:
    store = SQLAlchemyOAuthAccountStore(alchemy_config, oauth_protector)
    links = [
        await store.link(account_id, _identity(provider, f"{provider}-subject"), _grant(), _tokens(), now=NOW)
        for provider in ("github", "gitlab")
    ]

    outcomes = await asyncio.gather(
        *(
            store.unlink(account_id, link.provider, link.provider_account_id, require_remaining=True, now=NOW)
            for link in links
            for _ in range(CONTENDERS // 2)
        )
    )

    unlinked = [outcome.provider_account_id for outcome in outcomes if outcome.status is UnlinkStatus.UNLINKED]
    assert len(unlinked) == 1
    for link, outcome in zip([link for link in links for _ in range(CONTENDERS // 2)], outcomes, strict=True):
        if outcome.status is not UnlinkStatus.UNLINKED:
            removed = link.provider_account_id == unlinked[0]
            assert outcome.status is (UnlinkStatus.NOT_FOUND if removed else UnlinkStatus.FINAL_METHOD)
    async with alchemy_config.get_session() as db_session:
        assert await db_session.scalar(select(func.count()).select_from(m.UserOAuthAccount)) == 1


async def test_a_user_links_one_identity_per_provider(
    alchemy_config: SQLAlchemyAsyncConfig,
    oauth_protector: AESGCMOAuthTransactionProtector,
    account_id: str,
) -> None:
    store = SQLAlchemyOAuthAccountStore(alchemy_config, oauth_protector)

    links = await asyncio.gather(
        *(
            store.link(account_id, _identity("github", f"subject-{contender}"), _grant(), _tokens(), now=NOW)
            for contender in range(CONTENDERS)
        ),
        return_exceptions=True,
    )

    rejections = [link for link in links if isinstance(link, BaseException)]
    assert len(rejections) == CONTENDERS - 1
    assert all(isinstance(rejection, AccountLinkError) for rejection in rejections)
    with pytest.raises(AccountLinkError):
        await store.link(account_id, _identity("github", "another-subject"), _grant(), _tokens(), now=NOW)
    async with alchemy_config.get_session() as db_session:
        assert await db_session.scalar(select(func.count()).select_from(m.UserOAuthAccount)) == 1


async def test_concurrent_logins_provision_an_unknown_identity_once(
    alchemy_config: SQLAlchemyAsyncConfig,
    oauth_protector: AESGCMOAuthTransactionProtector,
    default_access_role: None,
) -> None:
    _ = default_access_role
    store = SQLAlchemyOAuthAccountStore(alchemy_config, oauth_protector)
    identities = [
        _identity("github", "new-subject", email=f"newcomer-{contender}@example.com") for contender in range(CONTENDERS)
    ]

    logins = await asyncio.gather(
        *(
            store.login(identity, _grant(), _tokens(), provision_unknown=True, retain_tokens=False, now=NOW)
            for identity in identities
        ),
        return_exceptions=True,
    )

    rejections = [login for login in logins if isinstance(login, BaseException)]
    assert len(rejections) == CONTENDERS - 1
    assert all(isinstance(rejection, AccountLinkError) for rejection in rejections)
    async with alchemy_config.get_session() as db_session:
        assert await db_session.scalar(select(func.count()).select_from(m.User)) == 1
        assert await db_session.scalar(select(func.count()).select_from(m.UserOAuthAccount)) == 1


async def test_concurrent_first_sign_ups_share_one_default_access_role(
    alchemy_config: SQLAlchemyAsyncConfig,
    oauth_protector: AESGCMOAuthTransactionProtector,
) -> None:
    store = SQLAlchemyOAuthAccountStore(alchemy_config, oauth_protector)
    identities = [
        _identity("github", f"first-subject-{contender}", email=f"first-{contender}@example.com")
        for contender in range(CONTENDERS)
    ]

    logins = await asyncio.gather(
        *(
            store.login(identity, _grant(), _tokens(), provision_unknown=True, retain_tokens=False, now=NOW)
            for identity in identities
        )
    )

    assert all(login.provisioned for login in logins)
    async with alchemy_config.get_session() as db_session:
        access_roles = select(func.count()).select_from(m.Role).where(m.Role.name == DEFAULT_ACCESS_ROLE)
        assert await db_session.scalar(access_roles) == 1
        assert await db_session.scalar(select(func.count()).select_from(m.UserRole)) == CONTENDERS


async def test_signing_in_again_invalidates_token_versions_read_before_it(
    alchemy_config: SQLAlchemyAsyncConfig,
    oauth_protector: AESGCMOAuthTransactionProtector,
    account_id: str,
) -> None:
    store = SQLAlchemyOAuthAccountStore(alchemy_config, oauth_protector)
    identity = _identity("github", "github-subject")
    link = await store.link(account_id, identity, _grant(), _tokens(), retain_tokens=True, now=NOW)
    read_before_login = await store.get_tokens(link.provider_account_id, now=NOW)
    assert read_before_login is not None

    await store.login(identity, _grant(), _tokens(), provision_unknown=False, retain_tokens=True, now=NOW)

    assert not await store.replace_tokens(
        link.provider_account_id,
        expected_version=read_before_login.reference.version,
        tokens=_tokens(),
        now=NOW,
    )


async def test_api_key_creation_tells_a_reused_key_id_from_an_unknown_account(
    alchemy_config: SQLAlchemyAsyncConfig,
    account_id: str,
) -> None:
    store = SQLAlchemyAPIKeyStore(alchemy_config)
    await store.create(_api_key("a2tra2tra2tra2tr", account_id))

    with pytest.raises(ValueError, match="already exists"):
        await store.create(_api_key("a2tra2tra2tra2tr", account_id))
    with pytest.raises(ValueError, match="subject does not exist"):
        await store.create(_api_key("b2trb2trb2trb2tr", _account_id("unknown-account", 0)))


async def test_revoking_an_api_key_that_already_stopped_working_leaves_it_untouched(
    alchemy_config: SQLAlchemyAsyncConfig,
    account_id: str,
) -> None:
    store = SQLAlchemyAPIKeyStore(alchemy_config)
    await store.create(_api_key("a2tra2tra2tra2tr", account_id))
    await store.create(_api_key("b2trb2trb2trb2tr", account_id))
    await store.revoke(key_id="a2tra2tra2tra2tr", now=NOW)
    await store.rotate(
        current_key_id="b2trb2trb2trb2tr",
        replacement=_api_key("c2trc2trc2trc2tr", account_id),
        overlap_until=NOW + timedelta(hours=1),
        now=NOW,
    )

    await store.revoke(key_id="a2tra2tra2tra2tr", now=NOW + timedelta(days=1))
    await store.revoke(key_id="b2trb2trb2trb2tr", now=NOW + timedelta(days=1))

    revoked = await store.get("a2tra2tra2tra2tr")
    rotated = await store.get("b2trb2trb2trb2tr")
    assert revoked is not None
    assert rotated is not None
    assert (revoked.revoked_at, revoked.overlap_until) == (NOW, None)
    assert (rotated.revoked_at, rotated.overlap_until) == (NOW, NOW + timedelta(hours=1))


async def test_revoking_a_rotated_api_key_ends_its_overlap(
    alchemy_config: SQLAlchemyAsyncConfig,
    account_id: str,
) -> None:
    store = SQLAlchemyAPIKeyStore(alchemy_config)
    await store.create(_api_key("a2tra2tra2tra2tr", account_id))
    await store.rotate(
        current_key_id="a2tra2tra2tra2tr",
        replacement=_api_key("b2trb2trb2trb2tr", account_id),
        overlap_until=NOW + timedelta(hours=1),
        now=NOW,
    )
    revoked_at = NOW + timedelta(minutes=30)

    await store.revoke(key_id="a2tra2tra2tra2tr", now=revoked_at)

    rotated = await store.get("a2tra2tra2tra2tr")
    assert rotated is not None
    assert (rotated.revoked_at, rotated.overlap_until) == (revoked_at, None)
    with pytest.raises(ValueError, match="does not exist"):
        await store.revoke(key_id="z2trz2trz2trz2tr", now=NOW)


async def test_identities_without_an_email_whose_subjects_differ_only_by_case_get_separate_accounts(
    alchemy_config: SQLAlchemyAsyncConfig,
    oauth_protector: AESGCMOAuthTransactionProtector,
) -> None:
    store = SQLAlchemyOAuthAccountStore(alchemy_config, oauth_protector)

    logins = [
        await store.login(
            _identity("example", subject), _grant(), _tokens(), provision_unknown=True, retain_tokens=False, now=NOW
        )
        for subject in ("AbC123", "abc123")
    ]

    assert all(login.provisioned for login in logins)
    async with alchemy_config.get_session() as db_session:
        emails = set(await db_session.scalars(select(m.User.email)))
    assert emails == {"example-416243313233@oauth.local", "example-616263313233@oauth.local"}
