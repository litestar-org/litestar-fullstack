"""Core foundation public-seam unit tests covering HKDF secrets, settings, models, migrations, and plugin stack."""

from __future__ import annotations

import importlib
import sqlite3
import sys
from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.alembic.commands import AlembicCommands
from advanced_alchemy.base import orm_registry
from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.stores.memory import MemoryStore
from litestar.testing import AsyncTestClient
from litestar_asyncapi import AsyncAPIConfig
from litestar_autowire import AutowireConfig, clear_autowire_cache
from litestar_email import EmailConfig
from litestar_email.backends.memory import InMemoryBackend
from litestar_granian import GranianPlugin
from litestar_mcp import LitestarMCP
from litestar_queues import QueueConfig, WorkerConfig
from litestar_security import SecurityPlugin
from litestar_vite import TypeGenConfig
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.pool import NullPool

from app import config
from app.db import models as m
from app.lib.secrets import (
    API_KEY_PEPPER_INFO,
    CSRF_SECRET_INFO,
    CURSOR_SECRET_INFO,
    OAUTH_PROTECTOR_INFO,
    PURPOSE_TOKEN_PEPPER_INFO,
    RECOVERY_CODE_PEPPER_INFO,
    SESSION_BINDING_PEPPER_INFO,
    SESSION_COOKIE_SECRET_INFO,
    TOTP_PROTECTOR_INFO,
    derive_subkey,
)
from app.lib.settings import (
    DatabaseSettings,
    LogSettings,
    MCPSettings,
    QueueSettings,
    ServerSettings,
    Settings,
    ViteSettings,
    get_settings,
)
from app.server.core import ApplicationCore
from app.server.plugins import build_plugins

if TYPE_CHECKING:
    from pathlib import Path

ALL_HKDF_INFO_LABELS = (
    SESSION_COOKIE_SECRET_INFO,
    PURPOSE_TOKEN_PEPPER_INFO,
    RECOVERY_CODE_PEPPER_INFO,
    TOTP_PROTECTOR_INFO,
    OAUTH_PROTECTOR_INFO,
    SESSION_BINDING_PEPPER_INFO,
    API_KEY_PEPPER_INFO,
    CSRF_SECRET_INFO,
    CURSOR_SECRET_INFO,
)


def test_hkdf_derive_subkey_deterministic_and_distinct() -> None:
    master = "super-secret-master-key-for-testing"
    first = derive_subkey(master, SESSION_COOKIE_SECRET_INFO)
    second = derive_subkey(master, SESSION_COOKIE_SECRET_INFO)
    assert first == second
    assert len(first) == 32

    derived = {derive_subkey(master, label) for label in ALL_HKDF_INFO_LABELS}
    assert len(derived) == len(ALL_HKDF_INFO_LABELS) == 9
    assert len(derive_subkey(master, CSRF_SECRET_INFO, length=64)) == 64


@pytest.mark.parametrize(
    ("secret", "info", "length"),
    [
        ("", SESSION_COOKIE_SECRET_INFO, 32),
        ("valid-secret", b"", 32),
        ("valid-secret", SESSION_COOKIE_SECRET_INFO, 15),
    ],
)
def test_hkdf_derive_subkey_rejects_invalid_inputs(secret: str, info: bytes, length: int) -> None:
    with pytest.raises(ValueError):
        derive_subkey(secret, info, length=length)


def test_settings_and_config_contracts() -> None:
    server = ServerSettings()
    assert server.APP_LOC == "app.server.asgi:create_app"
    assert server.LITESTAR_TRUSTED_PROXIES == []

    pg_db = DatabaseSettings(URL="postgresql://app:app@localhost:5432/app")
    assert pg_db.normalized_url() == "postgresql+asyncpg://app:app@localhost:5432/app"
    assert pg_db.is_postgres() is True
    pg_cfg = pg_db.get_config()
    assert pg_cfg.connection_string == "postgresql+asyncpg://app:app@localhost:5432/app"

    sqlite_db = DatabaseSettings(URL="sqlite+aiosqlite:///:memory:")
    assert sqlite_db.is_postgres() is False
    sqlite_cfg = sqlite_db.get_config()
    assert sqlite_cfg.engine_config.poolclass is NullPool

    disabled_pool_db = DatabaseSettings(URL="postgresql+asyncpg://app:app@localhost:5432/app", POOL_DISABLED=True)
    assert disabled_pool_db.get_config().engine_config.poolclass is NullPool

    queues = QueueSettings()
    assert queues.QUEUES == ("default", "emails", "reports", "maintenance")
    assert queues.EXECUTION_BACKEND == "local"
    assert queues.STREAM_ENABLED is True
    assert queues.STREAM_PATH == "/api/queues/events"
    assert queues.TERMINAL_RETENTION_SECONDS is None
    assert queues.ENABLE_PROMETHEUS is False
    assert queues.resolve_worker_wakeups(pg_db) is True
    assert queues.resolve_worker_wakeups(sqlite_db) is False
    assert QueueSettings(WORKER_WAKEUPS=True).resolve_worker_wakeups(sqlite_db) is False

    loaded = Settings.from_env(".env.nonexistent-for-test")
    assert loaded.email is not None
    assert loaded.queues is not None
    assert loaded.security is not None
    assert loaded.mcp is not None

    assert isinstance(config.asyncapi, AsyncAPIConfig)

    log_cfg = LogSettings().get_structlog_config()
    stdlib_cfg = log_cfg.structlog_logging_config.standard_lib_logging_config
    assert stdlib_cfg is not None
    stdlib_loggers = stdlib_cfg.loggers
    assert stdlib_loggers is not None
    assert "litestar_queues" in stdlib_loggers
    assert "saq" not in stdlib_loggers

    vite_cfg = ViteSettings().get_config()
    assert isinstance(vite_cfg.types, TypeGenConfig)
    assert vite_cfg.types.generate_channels is True


def test_models_metadata_and_deferred_columns() -> None:
    tables = set(orm_registry.metadata.tables.keys())
    expected_tables = {
        "user_account",
        "role",
        "user_account_role",
        "team",
        "team_member",
        "team_invitation",
        "tag",
        "team_tag",
        "audit_log",
        "user_account_oauth",
        "app_store",
        "auth_session",
        "auth_purpose_token",
        "auth_mfa_factor",
        "auth_mfa_recovery_code",
        "auth_mfa_login_challenge",
        "auth_step_up_grant",
        "auth_passkey",
        "auth_passkey_challenge",
        "auth_oauth_transaction",
        "auth_api_key",
        "queue_task",
        "queue_task_event_history",
        "queue_maintenance",
        "queue_task_reservation",
    }
    assert expected_tables.issubset(tables)
    assert "refresh_token" not in tables
    assert "email_verification_token" not in tables
    assert "password_reset_token" not in tables

    mapper = sa_inspect(m.User)
    assert mapper.column_attrs["hashed_password"].deferred is True
    assert mapper.column_attrs["hashed_password"].group == "security_sensitive"

    user = m.User(email="mfa@example.com")
    assert user.has_mfa is False
    user.mfa_factors = [
        m.UserMFAFactor(
            method_id="totp-1",
            secret_ciphertext=b"cipher",
            key_version="v1",
            is_confirmed=True,
        )
    ]
    assert user.has_mfa is True


def test_initial_alembic_migration_upgrade_downgrade_upgrade(tmp_path: Path) -> None:
    db_file = tmp_path / "migration_test.sqlite3"
    db_settings = DatabaseSettings(URL=f"sqlite+aiosqlite:///{db_file}")
    alchemy_cfg = db_settings.get_config()
    commands = AlembicCommands(sqlalchemy_config=alchemy_cfg)

    commands.upgrade(revision="head")
    commands.downgrade(revision="base")
    commands.upgrade(revision="head")

    with sqlite3.connect(db_file) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = {row[0] for row in rows}

    assert "user_account" in table_names
    assert "app_store" in table_names
    assert "auth_session" in table_names
    assert "auth_api_key" in table_names
    assert "queue_task" in table_names
    assert "refresh_token" not in table_names


def test_blank_env_strings_do_not_produce_empty_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LITESTAR_TRUSTED_PROXIES", "")
    monkeypatch.setenv("MCP_ALLOWED_ORIGINS", "")
    monkeypatch.setenv("QUEUES_POLL_INTERVAL", "")

    assert ServerSettings().LITESTAR_TRUSTED_PROXIES == []
    assert MCPSettings().ALLOWED_ORIGINS is None
    assert QueueSettings().POLL_INTERVAL == 0.25


def test_log_field_env_overrides_load(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_REQUEST_FIELDS", "path,method")
    monkeypatch.setenv("LOG_RESPONSE_FIELDS", '["status_code", "body"]')

    log_settings = LogSettings()

    assert log_settings.REQUEST_FIELDS == ["path", "method"]
    assert log_settings.RESPONSE_FIELDS == ["status_code", "body"]


def test_build_plugins_order_and_granian_static(monkeypatch: pytest.MonkeyPatch) -> None:
    built = build_plugins()
    assert len(built) == 11
    assert isinstance(built[-1], SecurityPlugin)
    assert any(isinstance(plugin, LitestarMCP) for plugin in built)
    granian_plugins = [plugin for plugin in built if isinstance(plugin, GranianPlugin)]
    assert len(granian_plugins) == 1
    assert getattr(granian_plugins[0], "static", getattr(granian_plugins[0], "_static", None)) == "auto"

    monkeypatch.setattr(get_settings().mcp, "ENABLED", False)
    built_without_mcp = build_plugins()
    assert len(built_without_mcp) == 10
    assert not any(isinstance(plugin, LitestarMCP) for plugin in built_without_mcp)
    assert isinstance(built_without_mcp[-1], SecurityPlugin)


@pytest.mark.anyio
async def test_application_core_autowire_di_and_proxy_headers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pkg_root = tmp_path / "fixture_domains"
    domain_dir = pkg_root / "sample"
    domain_dir.mkdir(parents=True)
    (pkg_root / "__init__.py").write_text("", encoding="utf-8")
    (domain_dir / "__init__.py").write_text("", encoding="utf-8")
    (domain_dir / "controllers.py").write_text(
        """from __future__ import annotations

from litestar import Controller, get
from litestar.di import NamedDependency
from litestar_email import EmailMessage, EmailService

from app.lib.email import AppEmailService
from app.lib.settings import AppSettings


class SampleController(Controller):
    path = "/api/sample"

    @get("/ping", opt={"exclude_from_auth": True})
    async def ping(
        self,
        settings: NamedDependency[AppSettings],
        mailer: NamedDependency[EmailService],
        app_mailer: NamedDependency[AppEmailService],
    ) -> dict[str, str]:
        await mailer.send_message(
            EmailMessage(
                subject="Ping",
                body="hello",
                to=["user@example.com"],
            )
        )
        return {
            "app": settings.NAME,
            "mailer_type": type(mailer).__name__,
            "app_mailer_type": type(app_mailer).__name__,
        }
""",
        encoding="utf-8",
    )
    (domain_dir / "jobs.py").write_text(
        """from __future__ import annotations

from litestar_queues import task


@task("sample.echo")
async def echo_task(value: str) -> str:
    return value
""",
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    clear_autowire_cache()
    InMemoryBackend.outbox.clear()

    try:
        email_cfg = EmailConfig(backend="memory", from_email="noreply@example.com")
        queue_cfg = QueueConfig(queue_backend="memory", worker=WorkerConfig(placement="asgi"))
        autowire_cfg = AutowireConfig(domain_packages=["fixture_domains"], integrations=["queues"])

        core = ApplicationCore(
            autowire_config=autowire_cfg,
            queue_config=queue_cfg,
            email_config=email_cfg,
        )
        probe_config = AppConfig()
        core.on_app_init(probe_config)

        reserved_security_keys = {
            "current_user",
            "principal",
            "security_context",
            "csp_nonce",
            "websocket_connect_tokens",
        }
        assert reserved_security_keys.isdisjoint(probe_config.dependencies.keys())

        app = Litestar(plugins=[core], stores={"sessions": MemoryStore()})

        middleware_before = list(app.middleware)
        assert not any(
            getattr(getattr(mw, "func", None), "__name__", None) == "wrap_asgi_with_proxy_headers"
            for mw in middleware_before
        )

        async with AsyncTestClient(app=app) as client:
            response = await client.get("/api/sample/ping")
            assert response.status_code == 200
            payload: dict[str, Any] = response.json()
            assert payload["mailer_type"] == "EmailService"
            assert payload["app_mailer_type"] == "AppEmailService"
            assert len(InMemoryBackend.outbox) == 1

        settings = get_settings()
        monkeypatch.setattr(settings.server, "LITESTAR_TRUSTED_PROXIES", ["127.0.0.1"])
        app_with_proxy = Litestar(
            plugins=[
                ApplicationCore(
                    autowire_config=autowire_cfg,
                    queue_config=queue_cfg,
                    email_config=email_cfg,
                )
            ]
        )
        assert any(
            getattr(getattr(mw, "func", None), "__name__", None) == "wrap_asgi_with_proxy_headers"
            for mw in app_with_proxy.middleware
        )
    finally:
        clear_autowire_cache()
        InMemoryBackend.outbox.clear()
        for name in list(sys.modules):
            if name == "fixture_domains" or name.startswith("fixture_domains."):
                sys.modules.pop(name, None)
