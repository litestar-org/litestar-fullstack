from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from httpx_oauth.oauth2 import OAuth2Token
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.accounts.guards import create_access_token
from app.lib.settings import get_settings
from tests.factories import UserFactory, UserOauthAccountFactory

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]


async def test_initiate_mfa_disable_oauth_success(
    client: AsyncClient, session: AsyncSession, monkeypatch: MonkeyPatch
) -> None:
    """Test successful initiation of MFA disable via OAuth."""
    settings = get_settings()
    # 1. Create a user without password but WITH MFA enabled and a linked OAuth account
    user = UserFactory.build(
        email=f"mfaoauth-{uuid4().hex[:8]}@example.com",
        hashed_password=None,  # No password
        is_two_factor_enabled=True,
        totp_secret="secret",
        two_factor_confirmed_at=None,
    )
    session.add(user)
    await session.commit()

    # Link a GitHub account
    oauth_account = UserOauthAccountFactory.build(user_id=user.id, oauth_name="github")
    session.add(oauth_account)
    await session.commit()

    # Mock GitHub OAuth settings
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    token = create_access_token(
        user_id=str(user.id), email=user.email, is_superuser=False, is_verified=True, auth_method="mfa"
    )

    response = await client.get("/api/mfa/disable/oauth/github", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert "authorizationUrl" in data
    assert "state" in data
    # Check that prompt=login is in the URL
    assert "prompt=login" in data["authorizationUrl"]


async def test_initiate_mfa_disable_oauth_with_password(
    client: AsyncClient, session: AsyncSession, monkeypatch: MonkeyPatch
) -> None:
    """Test that users WITH a password cannot use this flow."""
    settings = get_settings()
    user = UserFactory.build(
        email=f"mfapass-{uuid4().hex[:8]}@example.com",
        hashed_password="hashed_password",  # Has password
        is_two_factor_enabled=True,
    )
    session.add(user)
    await session.commit()

    # Link GitHub just in case
    oauth_account = UserOauthAccountFactory.build(user_id=user.id, oauth_name="github")
    session.add(oauth_account)
    await session.commit()

    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    token = create_access_token(
        user_id=str(user.id), email=user.email, is_superuser=False, is_verified=True, auth_method="mfa"
    )

    response = await client.get("/api/mfa/disable/oauth/github", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "Password verification required" in response.text


async def test_initiate_mfa_disable_oauth_no_linked_account(
    client: AsyncClient, session: AsyncSession, monkeypatch: MonkeyPatch
) -> None:
    """Test error when user has no linked account for the provider."""
    settings = get_settings()
    user = UserFactory.build(
        email=f"mfanooauth-{uuid4().hex[:8]}@example.com",
        hashed_password=None,
        is_two_factor_enabled=True,
    )
    session.add(user)
    await session.commit()

    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    token = create_access_token(
        user_id=str(user.id), email=user.email, is_superuser=False, is_verified=True, auth_method="mfa"
    )

    response = await client.get("/api/mfa/disable/oauth/github", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "No linked github account" in response.text


async def test_initiate_mfa_disable_oauth_provider_not_configured(
    client: AsyncClient, session: AsyncSession, monkeypatch: MonkeyPatch
) -> None:
    """Test error when provider is not configured."""
    user = UserFactory.build(hashed_password=None, is_two_factor_enabled=True)
    session.add(user)
    await session.commit()

    token = create_access_token(
        user_id=str(user.id), email=user.email, is_superuser=False, is_verified=True, auth_method="mfa"
    )

    response = await client.get("/api/mfa/disable/oauth/github", headers={"Authorization": f"Bearer {token}"})
    # Should probably be 400 or 404 depending on implementation
    assert response.status_code in {HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND}


async def test_callback_mfa_disable_success(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: MonkeyPatch,
) -> None:
    """Test successful MFA disable via OAuth callback."""
    settings = get_settings()
    from app.utils.oauth import create_oauth_state

    # 1. Create a user without password but WITH MFA enabled
    user = UserFactory.build(
        email=f"mfacallback-{uuid4().hex[:8]}@example.com",
        hashed_password=None,  # No password
        is_two_factor_enabled=True,
        totp_secret="secret",
        two_factor_confirmed_at=None,
    )
    session.add(user)
    await session.commit()

    # Link a GitHub account
    oauth_account = UserOauthAccountFactory.build(
        user_id=user.id, oauth_name="github", account_id="123456", account_email=user.email
    )
    session.add(oauth_account)
    await session.commit()

    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings.app, "GITHUB_OAUTH2_CLIENT_SECRET", "test-client-secret")

    # Create valid OAuth state with action="mfa_disable"
    state = create_oauth_state(
        provider="github",
        redirect_url="http://localhost:3000/oauth/github/callback",
        secret_key=settings.app.SECRET_KEY,
        action="mfa_disable",
        user_id=str(user.id),
    )

    async def mock_callback_call(*args: Any, **kwargs: Any) -> tuple[OAuth2Token, str]:
        return OAuth2Token({"access_token": "token", "token_type": "bearer", "expires_in": 3600}), state

    # Mock the OAuth2AuthorizeCallback.__call__ method
    with patch(
        "app.domain.accounts.controllers._oauth.OAuth2AuthorizeCallback.__call__", side_effect=mock_callback_call
    ):
        # Mock GitHub client get_id_email to return matching account
        async def mock_get_id_email(*args: Any, **kwargs: Any) -> tuple[str, str]:
            return "123456", user.email

        with patch("httpx_oauth.clients.github.GitHubOAuth2.get_id_email", side_effect=mock_get_id_email):
            # Make request to callback
            response = await client.get(
                f"/api/auth/oauth/github/callback?code=test-code&state={state}", follow_redirects=False
            )

            # Verify redirect to profile (success)
            # Depending on implementation, it might redirect to /profile or /settings
            assert response.status_code in {302, 307}
            # Should not have error
            assert "error=oauth_failed" not in response.headers["location"]

            # Verify MFA is disabled
            session.expire(user)
            await session.refresh(user, attribute_names=["totp_secret", "is_two_factor_enabled"])
            assert user.is_two_factor_enabled is False
            assert user.totp_secret is None
