"""Integration tests for ``litestar-security`` OAuth2/OIDC routes and transaction security."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

import pytest
from litestar import Litestar
from litestar.testing import AsyncTestClient
from litestar_email import EmailConfig

from app import config
from app.domain.accounts.security.config import build_security_config
from app.lib.settings import get_settings
from app.server.core import ApplicationCore

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]


def _build_oauth_app(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> Litestar:
    """Create a Litestar app with GitHub OAuth configured."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "URL", "https://app.example.test")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "gh-test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "gh-test-client-secret")

    queue_config = settings.queues.get_config(
        alchemy_config=config.alchemy,
        db_settings=settings.db,
        app_settings=settings.app,
    )
    security_config = build_security_config(settings, config.alchemy)
    app_instance = Litestar(
        plugins=[
            ApplicationCore(
                security_config=security_config,
                queue_config=queue_config,
                email_config=EmailConfig(backend="memory"),
            )
        ]
    )
    app_instance.state[config.alchemy.engine_app_state_key] = engine
    app_instance.state[config.alchemy.session_maker_app_state_key] = sessionmaker
    return app_instance


async def test_public_auth_config_reflects_enabled_oauth_providers(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_schema: None,
    _patch_db: None,
    db_cleanup: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``GET /api/config/auth`` reports configured OAuth providers, passkeys, and MFA flags."""
    _ = (db_schema, _patch_db, db_cleanup)
    oauth_app = _build_oauth_app(engine, sessionmaker, monkeypatch)
    async with AsyncTestClient(app=oauth_app) as client:
        response = await client.get("/api/config/auth")
        assert response.status_code == 200
        payload = response.json()
        assert payload["githubEnabled"] is True
        assert payload["passkeysEnabled"] is True
        assert payload["mfaEnabled"] is True


async def test_github_oauth_login_redirect_and_tampered_state_rejection(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_schema: None,
    _patch_db: None,
    db_cleanup: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GitHub login issues a signed redirect with state and rejects tampered callback state."""
    _ = (db_schema, _patch_db, db_cleanup)
    oauth_app = _build_oauth_app(engine, sessionmaker, monkeypatch)
    async with AsyncTestClient(app=oauth_app) as client:
        response = await client.get(
            "/api/auth/oauth/github/login",
            params={"return_to": "/home"},
            follow_redirects=False,
        )
        assert response.status_code in {302, 303, 307}, response.text
        location = response.headers.get("location", "")
        parsed = urlparse(location)
        assert "github.com" in parsed.netloc
        query = parse_qs(parsed.query)
        assert query.get("client_id") == ["gh-test-client-id"]
        assert "state" in query and len(query["state"][0]) > 10

        tampered = await client.get(
            "/api/auth/oauth/github/callback",
            params={"code": "fake-auth-code", "state": "tampered-invalid-state"},
            follow_redirects=False,
        )
        assert tampered.status_code in {400, 401, 403}, tampered.text

        missing_state = await client.get(
            "/api/auth/oauth/github/callback",
            params={"code": "fake-auth-code"},
            follow_redirects=False,
        )
        assert missing_state.status_code in {400, 401, 403}, missing_state.text


async def test_oauth_disallowed_return_to_rejected(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_schema: None,
    _patch_db: None,
    db_cleanup: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disallowed external ``return_to`` URLs are rejected by ``OAuthRedirectPolicy``."""
    _ = (db_schema, _patch_db, db_cleanup)
    oauth_app = _build_oauth_app(engine, sessionmaker, monkeypatch)
    async with AsyncTestClient(app=oauth_app) as client:
        response = await client.get(
            "/api/auth/oauth/github/login",
            params={"return_to": "https://evil.example/phish"},
            follow_redirects=False,
        )
        assert response.status_code in {400, 401, 403, 422}, response.text


async def test_oauth_accounts_list_requires_authentication(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_schema: None,
    _patch_db: None,
    db_cleanup: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linking an OAuth account fails closed for unauthenticated callers."""
    _ = (db_schema, _patch_db, db_cleanup)
    oauth_app = _build_oauth_app(engine, sessionmaker, monkeypatch)
    async with AsyncTestClient(app=oauth_app) as client:
        await client.get("/api/config/auth")
        csrf = client.cookies.get("XSRF-TOKEN") or ""
        unauth: Any = await client.post(
            "/api/auth/oauth/github/link",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert unauth.status_code == 401
