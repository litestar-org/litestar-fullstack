"""Unified litestar-security store conformance and compiled route posture suite."""

from __future__ import annotations

import warnings
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from click.testing import CliRunner
from litestar import Litestar
from litestar.cli._utils import LitestarEnv
from litestar.cli.main import litestar_group
from litestar.openapi.config import OpenAPIConfig
from litestar_security import SecurityPlugin
from litestar_security.accounts import RateLimitPolicy
from litestar_security.testing import (
    StoreConformanceFactories,
    assert_api_key_store_conformance,
    assert_oauth_transaction_protector_conformance,
    assert_rate_limiter_conformance,
    assert_secret_protector_conformance,
    assert_security_backend_conformance,
    assert_session_registry_conformance,
)
from sqlalchemy import select

from app.db import models as m
from app.domain.accounts.controllers import (
    ApiKeyController,
    ProfileController,
    RoleController,
    UserController,
)
from app.domain.accounts.security import (
    SQLAlchemyAPIKeyStore,
    SQLAlchemyMFALoginChallengeService,
    SQLAlchemyMFAService,
    SQLAlchemyOAuthAccountStore,
    SQLAlchemyOAuthTransactionStore,
    SQLAlchemyPasskeyStore,
    SQLAlchemySecurityBackend,
    SQLAlchemyStepUpService,
    build_csrf_config,
    build_oauth_protector,
    build_rate_limiter,
    build_secret_protector,
    build_security_config,
    build_session_middleware,
)
from app.lib.settings import AppSettings, DatabaseSettings, SecuritySettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio

DEFAULT_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _uuid_id(namespace: str, sequence: int) -> str:
    return str(uuid5(NAMESPACE_DNS, f"{namespace}:{sequence}"))


async def _make_db(tmp_path: Path, name: str) -> SQLAlchemyAsyncConfig:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)
    return db_cfg


async def _seed_conformance_users(cfg: SQLAlchemyAsyncConfig) -> None:
    namespaces = (
        "conformance-account",
        "conformance-principal",
        "conformance-session-other",
        "conformance-session-owner",
        "conformance-subject",
    )
    async with cfg.get_session() as session:
        for ns in namespaces:
            uid = UUID(_uuid_id(ns, 0))
            if await session.scalar(select(m.User.id).where(m.User.id == uid)) is None:
                session.add(m.User(id=uid, email=f"{uid}@example.com", is_active=True, is_verified=True))
        await session.commit()


async def test_unified_security_conformance_suites(tmp_path: Path) -> None:
    settings = Settings(app=AppSettings(SECRET_KEY="conformance-master-secret"))
    await assert_secret_protector_conformance(lambda: build_secret_protector(settings))
    await assert_oauth_transaction_protector_conformance(lambda: build_oauth_protector(settings))

    configs: list[SQLAlchemyAsyncConfig] = []

    async def make_pool(prefix: str, count: int) -> list[SQLAlchemyAsyncConfig]:
        pool: list[SQLAlchemyAsyncConfig] = []
        for idx in range(1, count + 1):
            cfg = await _make_db(tmp_path, f"{prefix}_{idx}.sqlite3")
            configs.append(cfg)
            await _seed_conformance_users(cfg)
            pool.append(cfg)
        return pool

    backend_iter = iter([SQLAlchemySecurityBackend(c, clock=lambda: DEFAULT_NOW) for c in await make_pool("b", 8)])
    mfa_iter = iter([SQLAlchemyMFAService(c) for c in await make_pool("mfa", 8)])
    chal_iter = iter([SQLAlchemyMFALoginChallengeService(c) for c in await make_pool("chal", 8)])
    step_iter = iter([SQLAlchemyStepUpService(c) for c in await make_pool("step", 8)])
    pk_iter = iter([SQLAlchemyPasskeyStore(c) for c in await make_pool("pk", 8)])
    pk_chal_iter = iter([SQLAlchemyPasskeyStore(c) for c in await make_pool("pkc", 8)])
    protector = build_oauth_protector(settings)
    otx_iter = iter([SQLAlchemyOAuthTransactionStore(c, protector) for c in await make_pool("otx", 8)])
    oacc_iter = iter([SQLAlchemyOAuthAccountStore(c, protector) for c in await make_pool("oacc", 8)])
    api_iter = iter([SQLAlchemyAPIKeyStore(c) for c in await make_pool("api", 8)])

    db_rate = await _make_db(tmp_path, "conf_rate.sqlite3")
    configs.append(db_rate)

    try:
        await assert_security_backend_conformance(
            StoreConformanceFactories(
                local_account_store=cast("Any", lambda: next(backend_iter)),
                session_registry=lambda: next(backend_iter),
                mfa_store=lambda: next(mfa_iter),
                mfa_login_challenge_store=lambda: next(chal_iter),
                step_up_store=lambda: next(step_iter),
                passkey_store=lambda: next(pk_iter),
                webauthn_challenge_store=lambda: next(pk_chal_iter),
                oauth_transaction_store=lambda: next(otx_iter),
                oauth_account_store=lambda: next(oacc_iter),
            ),
            identifiers=_uuid_id,
        )
        await assert_session_registry_conformance(
            lambda: next(backend_iter),
            now=DEFAULT_NOW,
            identifiers=_uuid_id,
        )
        await assert_api_key_store_conformance(
            lambda: next(api_iter),
            identifiers=_uuid_id,
        )
        await assert_rate_limiter_conformance(
            lambda limit: build_rate_limiter(
                db_rate,
                policies={"conformance.rate_limit": RateLimitPolicy(limit=limit, window=timedelta(seconds=60))},
                clock=lambda: DEFAULT_NOW,
            ),
            limit=5,
            concurrency=20,
        )
    finally:
        for cfg in configs:
            await cfg.get_engine().dispose()


def test_security_routes_posture_and_cli_inspection(tmp_path: Path) -> None:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / 'posture.sqlite3'}").get_config()
    settings = Settings(
        app=AppSettings(SECRET_KEY="posture-test-secret", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
    )
    sec_cfg = build_security_config(settings, db_cfg)
    assert sec_cfg.exclude is not None
    assert sec_cfg.exclude == ("^/static",)
    for forbidden_exclude in ("/docs", "/schema", "/.well-known"):
        assert all(forbidden_exclude not in pattern for pattern in sec_cfg.exclude)

    security_plugin = SecurityPlugin(sec_cfg)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        app = Litestar(
            route_handlers=[ProfileController, ApiKeyController, UserController, RoleController],
            plugins=[SQLAlchemyPlugin(config=db_cfg), security_plugin],
            middleware=[build_session_middleware(settings)],
            csrf_config=build_csrf_config(settings),
            openapi_config=OpenAPIConfig(title="Accounts Posture Test", version="0.1.0"),
        )

    security_warnings = [w for w in caught if "exclude" in str(w.message).lower() or "csrf" in str(w.message).lower()]
    assert security_warnings == []

    cli = litestar_group
    security_plugin.on_cli_init(cli)
    runner = CliRunner()
    result = runner.invoke(cli, ["security", "routes"], obj=LitestarEnv(app_path="test:app", app=app, cwd=tmp_path))
    assert result.exit_code == 0, result.output
    assert "/api/me" in result.output
    assert "/api/me/api-keys" in result.output
    assert "/api/users" in result.output
    assert "/api/roles" in result.output
    assert "/api/access/login" in result.output
