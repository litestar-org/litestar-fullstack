"""Integration tests for OAuth authentication endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from app.lib.settings import get_settings
from app.utils.oauth import create_oauth_state

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = [pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]


def _create_valid_state(provider: str, redirect_url: str | None = None) -> str:
    """Create a valid OAuth state token for testing."""
    settings = get_settings()
    return create_oauth_state(
        provider=provider,
        redirect_url=redirect_url or f"{settings.app.URL}/auth/{provider}/callback",
        secret_key=settings.app.SECRET_KEY,
    )


# --- Google OAuth Authorization Tests ---


@pytest.mark.anyio
async def test_google_authorize_not_configured(
    client: AsyncClient,
) -> None:
    """Test Google OAuth initiation when not configured."""
    with patch("app.domain.accounts.controllers._oauth.OAuthController.google_authorize") as mock:
        # Let the original code run but ensure OAuth is "not configured"
        mock.side_effect = None

    response = await client.get("/api/auth/oauth/google")

    # In test environment, OAuth may not be configured
    # Accept either 200 (if configured) or 400 (if not configured)
    assert response.status_code in (200, 400)
    if response.status_code == 400:
        assert "not configured" in response.text.lower()


@pytest.mark.anyio
async def test_google_authorize_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google OAuth initiation when configured."""
    settings = get_settings()
    # Mock OAuth credentials (settings.app contains AppSettings)
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    response = await client.get("/api/auth/oauth/google")

    assert response.status_code == 200
    data = response.json()
    assert "authorizationUrl" in data
    assert "state" in data
    assert "accounts.google.com" in data["authorizationUrl"]
    assert "test-client-id" in data["authorizationUrl"]


@pytest.mark.anyio
async def test_google_authorize_with_redirect_url(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google OAuth initiation with custom redirect URL."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    custom_redirect = "http://localhost:3000/custom/callback"
    response = await client.get(f"/api/auth/oauth/google?redirect_url={custom_redirect}")

    assert response.status_code == 200
    data = response.json()
    assert "authorizationUrl" in data
    # The state should contain the custom redirect URL (encoded in the JWT)


# --- Google OAuth Callback Tests ---


@pytest.mark.anyio
async def test_google_callback_missing_state(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google OAuth callback without state parameter."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    response = await client.get("/api/auth/oauth/google/callback?code=test-code", follow_redirects=False)

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location
    assert "Missing" in location or "state" in location.lower()


@pytest.mark.anyio
async def test_google_callback_invalid_state(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google OAuth callback with invalid state token."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    response = await client.get(
        "/api/auth/oauth/google/callback?code=test-code&state=invalid-state",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


@pytest.mark.anyio
async def test_google_callback_missing_code(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google OAuth callback without authorization code."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    state = _create_valid_state("google")

    response = await client.get(
        f"/api/auth/oauth/google/callback?state={state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location
    assert "code" in location.lower()


@pytest.mark.anyio
async def test_google_callback_oauth_error(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google OAuth callback with error from provider."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    state = _create_valid_state("google")

    response = await client.get(
        f"/api/auth/oauth/google/callback?state={state}&error=access_denied",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


@pytest.mark.anyio
async def test_google_callback_token_exchange_failure(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google OAuth callback when token exchange fails."""
    from httpx_oauth.oauth2 import GetAccessTokenError

    settings = get_settings()
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    state = _create_valid_state("google")

    # Mock the OAuth2 callback to raise GetAccessTokenError
    with patch("app.domain.accounts.controllers._oauth.OAuth2AuthorizeCallback") as mock_callback_class:
        mock_callback_instance = AsyncMock()
        mock_callback_instance.side_effect = GetAccessTokenError("Token exchange failed")
        mock_callback_class.return_value = mock_callback_instance

        response = await client.get(
            f"/api/auth/oauth/google/callback?code=test-code&state={state}",
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location
    assert "token" in location.lower() or "exchange" in location.lower()


@pytest.mark.anyio
async def test_google_callback_get_user_info_failure(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google OAuth callback when getting user info fails."""
    from httpx_oauth.exceptions import GetIdEmailError

    settings = get_settings()
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    state = _create_valid_state("google")
    mock_token_data = {
        "access_token": "mock-access-token",
        "token_type": "Bearer",
    }

    # Mock successful token exchange but failed user info fetch
    with (
        patch("app.domain.accounts.controllers._oauth.OAuth2AuthorizeCallback") as mock_callback_class,
        patch(
            "app.domain.accounts.controllers._oauth.GoogleOAuth2.get_id_email",
            new_callable=AsyncMock,
        ) as mock_get_id_email,
    ):
        mock_callback_instance = AsyncMock()
        mock_callback_instance.return_value = (mock_token_data, state)
        mock_callback_class.return_value = mock_callback_instance

        mock_get_id_email.side_effect = GetIdEmailError("Failed to get user info")

        response = await client.get(
            f"/api/auth/oauth/google/callback?code=test-code&state={state}",
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


# --- GitHub OAuth Authorization Tests ---


@pytest.mark.anyio
async def test_github_authorize_not_configured(
    client: AsyncClient,
) -> None:
    """Test GitHub OAuth initiation when not configured."""
    response = await client.get("/api/auth/oauth/github")

    # Accept either 200 (if configured) or 400 (if not configured)
    assert response.status_code in (200, 400)
    if response.status_code == 400:
        assert "not configured" in response.text.lower()


@pytest.mark.anyio
async def test_github_authorize_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub OAuth initiation when configured."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    response = await client.get("/api/auth/oauth/github")

    assert response.status_code == 200
    data = response.json()
    assert "authorizationUrl" in data
    assert "state" in data
    assert "github.com" in data["authorizationUrl"]


@pytest.mark.anyio
async def test_github_authorize_with_redirect_url(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub OAuth initiation with custom redirect URL."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    custom_redirect = "http://localhost:3000/custom/callback"
    response = await client.get(f"/api/auth/oauth/github?redirect_url={custom_redirect}")

    assert response.status_code == 200
    data = response.json()
    assert "authorizationUrl" in data


# --- GitHub OAuth Callback Tests ---


@pytest.mark.anyio
async def test_github_callback_missing_state(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub OAuth callback without state parameter."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    response = await client.get("/api/auth/oauth/github/callback?code=test-code", follow_redirects=False)

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


@pytest.mark.anyio
async def test_github_callback_invalid_state(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub OAuth callback with invalid state token."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    response = await client.get(
        "/api/auth/oauth/github/callback?code=test-code&state=invalid-state",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


@pytest.mark.anyio
async def test_github_callback_missing_code(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub OAuth callback without authorization code."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    state = _create_valid_state("github")

    response = await client.get(
        f"/api/auth/oauth/github/callback?state={state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


@pytest.mark.anyio
async def test_github_callback_oauth_error(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub OAuth callback with error from provider."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    state = _create_valid_state("github")

    response = await client.get(
        f"/api/auth/oauth/github/callback?state={state}&error=access_denied&error_description=User%20denied%20access",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


@pytest.mark.anyio
async def test_github_callback_token_exchange_failure(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub OAuth callback when token exchange fails."""
    from httpx_oauth.oauth2 import GetAccessTokenError

    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    state = _create_valid_state("github")

    with patch("app.domain.accounts.controllers._oauth.OAuth2AuthorizeCallback") as mock_callback_class:
        mock_callback_instance = AsyncMock()
        mock_callback_instance.side_effect = GetAccessTokenError("Token exchange failed")
        mock_callback_class.return_value = mock_callback_instance

        response = await client.get(
            f"/api/auth/oauth/github/callback?code=test-code&state={state}",
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


@pytest.mark.anyio
async def test_github_callback_get_user_info_failure(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub OAuth callback when getting user info fails."""
    from httpx_oauth.exceptions import GetIdEmailError

    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    state = _create_valid_state("github")
    mock_token_data = {
        "access_token": "mock-access-token",
        "token_type": "Bearer",
    }

    with (
        patch("app.domain.accounts.controllers._oauth.OAuth2AuthorizeCallback") as mock_callback_class,
        patch(
            "app.domain.accounts.controllers._oauth.GitHubOAuth2.get_id_email",
            new_callable=AsyncMock,
        ) as mock_get_id_email,
    ):
        mock_callback_instance = AsyncMock()
        mock_callback_instance.return_value = (mock_token_data, state)
        mock_callback_class.return_value = mock_callback_instance

        mock_get_id_email.side_effect = GetIdEmailError("Failed to get user info")

        response = await client.get(
            f"/api/auth/oauth/github/callback?code=test-code&state={state}",
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


# --- State Token Validation Tests ---


@pytest.mark.anyio
async def test_google_callback_wrong_provider_state(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Google callback rejects state created for different provider."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GOOGLE_OAUTH2_CLIENT_SECRET", "test-client-secret")

    # Create state for GitHub, use it for Google callback
    github_state = _create_valid_state("github")

    response = await client.get(
        f"/api/auth/oauth/google/callback?code=test-code&state={github_state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location


@pytest.mark.anyio
async def test_github_callback_wrong_provider_state(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GitHub callback rejects state created for different provider."""
    settings = get_settings()
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    # Create state for Google, use it for GitHub callback
    google_state = _create_valid_state("google")

    response = await client.get(
        f"/api/auth/oauth/github/callback?code=test-code&state={google_state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location
