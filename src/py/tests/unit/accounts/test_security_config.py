"""Unit tests for build_security_config, HKDF isolation, notification callbacks, and SecurityPlugin boot."""

from __future__ import annotations

import warnings
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar_queues import QueueConfig, QueueService, WorkerConfig, task
from litestar_security import SecurityPlugin
from litestar_security.accounts import NotificationCommand
from litestar_security.providers.oauth import OAuthLifecycleService

from app import config as app_config_module
from app.domain.accounts.security import (
    build_csrf_config,
    build_notification_handler,
    build_security_config,
    build_session_middleware,
    build_session_store,
)
from app.lib.settings import AppSettings, DatabaseSettings, SecuritySettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.anyio


def test_security_config_cookie_flags_and_exclusions(tmp_path: Path) -> None:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / 'sec_cfg.sqlite3'}").get_config()

    dev_settings = Settings(
        app=AppSettings(SECRET_KEY="test-secret-dev", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
    )
    dev_cfg = build_security_config(dev_settings, db_cfg)
    assert dev_cfg.exclude == ("^/static",)
    assert dev_cfg.headers is not None
    assert dev_cfg.local_auth is not None
    assert dev_cfg.local_auth.binding is not None
    assert dev_cfg.local_auth.binding.cookie_name == "app-binding"
    assert dev_cfg.local_auth.binding.allow_insecure is True
    assert dev_cfg.local_auth.route_prefix == "/api/access"
    assert dev_cfg.mfa is not None
    assert dev_cfg.mfa.require_at_login == "enrolled"
    assert dev_cfg.mfa.route_prefix == "/api/access"
    assert dev_cfg.passkeys is not None
    assert dev_cfg.passkeys.route_prefix == "/api/access"
    assert dev_cfg.oauth is None
    assert dev_cfg.api_key is not None
    assert dev_cfg.protected_resource is not None

    prod_settings = Settings(
        app=AppSettings(
            SECRET_KEY="test-secret-prod",
            URL="https://app.example.com",
            COOKIE_SECURE=True,
            GITHUB_OAUTH2_CLIENT_ID="gh-client-id",
            GITHUB_OAUTH2_CLIENT_SECRET="gh-client-secret",
            GOOGLE_OAUTH2_CLIENT_ID="google-client-id",
            GOOGLE_OAUTH2_CLIENT_SECRET="google-client-secret",
        ),
        security=SecuritySettings(
            COOKIE_SECURE=True,
            PASSKEY_RP_ID="app.example.com",
            PASSKEY_ORIGINS=["https://app.example.com"],
        ),
    )
    prod_cfg = build_security_config(prod_settings, db_cfg)
    assert prod_cfg.local_auth is not None
    assert prod_cfg.local_auth.binding is not None
    assert prod_cfg.local_auth.binding.cookie_name == "__Host-app-binding"
    assert prod_cfg.local_auth.binding.allow_insecure is False
    assert prod_cfg.oauth is not None
    assert prod_cfg.oauth.route_prefix == "/api/auth/oauth"
    oauth_service = prod_cfg.oauth.oauth_service
    assert isinstance(oauth_service, OAuthLifecycleService)
    assert set(oauth_service.provider_names) == {"github", "google"}
    assert oauth_service._registration("github").expected_issuer == "https://github.com"
    assert oauth_service._registration("google").expected_issuer == "https://accounts.google.com"
    assert oauth_service.step_up is not None
    assert len(prod_cfg.jwks_providers) == 1
    assert prod_cfg.jwks_warmup_failure == "lazy"

    google_only_settings = Settings(
        app=AppSettings(
            SECRET_KEY="test-secret-google",
            URL="https://app.example.com",
            COOKIE_SECURE=True,
            GOOGLE_OAUTH2_CLIENT_ID="google-only-id",
            GOOGLE_OAUTH2_CLIENT_SECRET="google-only-secret",
        ),
        security=SecuritySettings(COOKIE_SECURE=True, PASSKEY_RP_ID="app.example.com"),
    )
    google_only_cfg = build_security_config(google_only_settings, db_cfg)
    assert google_only_cfg.oauth is not None
    assert isinstance(google_only_cfg.oauth.oauth_service, OAuthLifecycleService)
    assert set(google_only_cfg.oauth.oauth_service.provider_names) == {"google"}

    assert app_config_module.security.api_key is not None
    assert app_config_module.mcp.auth is not None


async def test_notification_handler_enqueues_canonical_email_tasks() -> None:
    @task("email.send_verification", queue="emails")
    async def _send_verification(email: str, token: str, expires_at: str, return_url: str | None = None) -> None:
        _ = (email, token, expires_at, return_url)

    @task("email.send_password_reset", queue="emails")
    async def _send_password_reset(email: str, token: str, expires_at: str, return_url: str | None = None) -> None:
        _ = (email, token, expires_at, return_url)

    @task("email.send_password_reset_confirmation", queue="emails")
    async def _send_password_reset_confirmation(
        email: str, token: str, expires_at: str, return_url: str | None = None
    ) -> None:
        _ = (email, token, expires_at, return_url)

    queue_service = QueueService(
        config=QueueConfig(
            queue_backend="memory",
            worker=WorkerConfig(placement="asgi"),
        )
    )
    await queue_service.open()
    try:
        handler = build_notification_handler(queue_service=queue_service)
        now = datetime.now(UTC)
        for template, expected_task in (
            ("local.verify", "email.send_verification"),
            ("local.recovery", "email.send_password_reset"),
            ("password_reset_confirmation", "email.send_password_reset_confirmation"),
        ):
            await handler(
                NotificationCommand(
                    template=template,
                    destination="user@example.com",
                    token="opaque-token-value",
                    expires_at=now + timedelta(hours=1),
                    return_url="https://app.example.com/auth/verify",
                )
            )
            page = await queue_service.list_tasks(task_name=expected_task)
            assert len(page.items) == 1
            assert page.items[0].queue == "emails"
    finally:
        await queue_service.close()


def test_security_plugin_boots_with_zero_litestar_warnings(tmp_path: Path) -> None:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / 'sec_boot.sqlite3'}").get_config()
    settings = Settings(
        app=AppSettings(SECRET_KEY="boot-test-secret", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
    )
    sec_cfg = build_security_config(settings, db_cfg)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        app = Litestar(
            plugins=[SecurityPlugin(sec_cfg)],
            middleware=[build_session_middleware(settings)],
            csrf_config=build_csrf_config(settings),
            stores={"sessions": build_session_store(db_cfg)},
            openapi_config=OpenAPIConfig(title="Test", version="0.1.0"),
        )
    assert app is not None
    security_warnings = [w for w in caught if "exclude" in str(w.message).lower() or "csrf" in str(w.message).lower()]
    assert security_warnings == []
