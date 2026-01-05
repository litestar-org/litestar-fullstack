"""Comprehensive tests for OAuth utilities."""

from __future__ import annotations

import time
from unittest.mock import Mock

import jwt
import pytest
from litestar.exceptions import HTTPException

from app.utils.oauth import (
    OAUTH_STATE_EXPIRY_SECONDS,
    OAuth2AuthorizeCallback,
    OAuth2AuthorizeCallbackError,
    OAuth2ProviderPlugin,
    build_oauth_error_redirect,
    create_oauth_state,
    verify_oauth_state,
)

pytestmark = [pytest.mark.unit, pytest.mark.oauth, pytest.mark.security]


def test_create_basic_state() -> None:
    """Test creating a basic OAuth state token."""
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key="test-secret-key",
    )

    assert state is not None
    assert isinstance(state, str)
    assert len(state) > 0


def test_state_decodes_correctly() -> None:
    """Test that state token decodes correctly."""
    secret_key = "test-secret-key"
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
    )

    payload = jwt.decode(state, secret_key, algorithms=["HS256"])

    assert payload["provider"] == "google"
    assert payload["redirect_url"] == "http://localhost:3000/callback"
    assert "exp" in payload
    assert "iat" in payload


def test_state_with_action() -> None:
    """Test creating state with action parameter."""
    secret_key = "test-secret-key"
    state = create_oauth_state(
        provider="github",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
        action="link",
    )

    payload = jwt.decode(state, secret_key, algorithms=["HS256"])

    assert payload["action"] == "link"


def test_state_with_user_id() -> None:
    """Test creating state with user_id parameter."""
    secret_key = "test-secret-key"
    user_id = "user-123-abc"
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
        user_id=user_id,
    )

    payload = jwt.decode(state, secret_key, algorithms=["HS256"])

    assert payload["user_id"] == user_id


def test_state_expiration() -> None:
    """Test that state has correct expiration time."""
    secret_key = "test-secret-key"
    before = int(time.time())
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
    )
    after = int(time.time())

    payload = jwt.decode(state, secret_key, algorithms=["HS256"])

    expected_min = before + OAUTH_STATE_EXPIRY_SECONDS
    expected_max = after + OAUTH_STATE_EXPIRY_SECONDS

    assert expected_min <= payload["exp"] <= expected_max


def test_state_issued_at() -> None:
    """Test that state has correct issued at time."""
    secret_key = "test-secret-key"
    before = int(time.time())
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
    )
    after = int(time.time())

    payload = jwt.decode(state, secret_key, algorithms=["HS256"])

    assert before <= payload["iat"] <= after


def test_valid_state() -> None:
    """Test verifying a valid state token."""
    secret_key = "test-secret-key"
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
    )

    is_valid, payload, error = verify_oauth_state(
        state=state,
        expected_provider="google",
        secret_key=secret_key,
    )

    assert is_valid is True
    assert payload["provider"] == "google"
    assert error == ""


def test_wrong_provider() -> None:
    """Test verifying state with wrong provider."""
    secret_key = "test-secret-key"
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
    )

    is_valid, payload, error = verify_oauth_state(
        state=state,
        expected_provider="github",  # Wrong provider
        secret_key=secret_key,
    )

    assert is_valid is False
    assert payload == {}
    assert "Invalid OAuth provider" in error


def test_wrong_secret_key() -> None:
    """Test verifying state with wrong secret key."""
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key="correct-secret",
    )

    is_valid, payload, error = verify_oauth_state(
        state=state,
        expected_provider="google",
        secret_key="wrong-secret",
    )

    assert is_valid is False
    assert payload == {}
    assert "Invalid OAuth state" in error


def test_expired_state() -> None:
    """Test verifying an expired state token."""
    secret_key = "test-secret-key"
    # Create a token that's already expired
    expired_payload = {
        "provider": "google",
        "redirect_url": "http://localhost:3000/callback",
        "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        "iat": int(time.time()) - 4200,
    }
    state = jwt.encode(expired_payload, secret_key, algorithm="HS256")

    is_valid, payload, error = verify_oauth_state(
        state=state,
        expected_provider="google",
        secret_key=secret_key,
    )

    assert is_valid is False
    assert payload == {}
    assert "expired" in error.lower()


def test_invalid_token() -> None:
    """Test verifying an invalid token."""
    is_valid, payload, error = verify_oauth_state(
        state="not-a-valid-jwt",
        expected_provider="google",
        secret_key="test-secret",
    )

    assert is_valid is False
    assert payload == {}
    assert "Invalid OAuth state" in error


def test_state_with_action_preserved() -> None:
    """Test that action is preserved in verified payload."""
    secret_key = "test-secret-key"
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
        action="upgrade",
    )

    is_valid, payload, _error = verify_oauth_state(
        state=state,
        expected_provider="google",
        secret_key=secret_key,
    )

    assert is_valid is True
    assert payload["action"] == "upgrade"


def test_state_with_user_id_preserved() -> None:
    """Test that user_id is preserved in verified payload."""
    secret_key = "test-secret-key"
    state = create_oauth_state(
        provider="google",
        redirect_url="http://localhost:3000/callback",
        secret_key=secret_key,
        user_id="user-456",
    )

    is_valid, payload, _error = verify_oauth_state(
        state=state,
        expected_provider="google",
        secret_key=secret_key,
    )

    assert is_valid is True
    assert payload["user_id"] == "user-456"


def test_simple_redirect() -> None:
    """Test building simple error redirect URL."""
    result = build_oauth_error_redirect(
        base_url="http://localhost:3000/callback",
        error="access_denied",
        message="User denied access",
    )

    assert "http://localhost:3000/callback" in result
    assert "error=access_denied" in result
    assert "message=User" in result


def test_redirect_with_existing_query_params() -> None:
    """Test building redirect URL when base URL already has query params."""
    result = build_oauth_error_redirect(
        base_url="http://localhost:3000/callback?existing=param",
        error="server_error",
        message="Something went wrong",
    )

    assert "http://localhost:3000/callback?existing=param" in result
    assert "&error=server_error" in result
    assert "&message=" in result


def test_redirect_without_existing_query_params() -> None:
    """Test building redirect URL when base URL has no query params."""
    result = build_oauth_error_redirect(
        base_url="http://localhost:3000/callback",
        error="invalid_request",
        message="Bad request",
    )

    assert "?error=" in result
    # Shouldn't have double question marks
    assert "??" not in result


def test_url_encodes_special_characters() -> None:
    """Test that special characters are URL encoded."""
    result = build_oauth_error_redirect(
        base_url="http://localhost:3000/callback",
        error="error_code",
        message="Message with spaces & special chars!",
    )

    # Special characters should be URL encoded
    assert "+" in result or "%20" in result  # Space encoding
    assert "%26" in result or "amp" in result  # & encoding


def test_basic_error() -> None:
    """Test creating a basic callback error."""
    error = OAuth2AuthorizeCallbackError(
        status_code=400,
        detail="Invalid code",
    )

    assert error.status_code == 400
    assert error.detail == "Invalid code"
    assert error.response is None


def test_error_with_response() -> None:
    """Test creating error with response object."""
    mock_response = Mock()
    error = OAuth2AuthorizeCallbackError(
        status_code=500,
        detail="Server error",
        response=mock_response,
    )

    assert error.status_code == 500
    assert error.response is mock_response


def test_error_with_headers() -> None:
    """Test creating error with custom headers."""
    error = OAuth2AuthorizeCallbackError(
        status_code=401,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )

    assert error.status_code == 401
    assert error.headers is not None
    assert "WWW-Authenticate" in error.headers


def test_error_with_extra() -> None:
    """Test creating error with extra data."""
    error = OAuth2AuthorizeCallbackError(
        status_code=400,
        detail="Bad request",
        extra={"field": "code", "reason": "expired"},
    )

    assert error.extra == {"field": "code", "reason": "expired"}


def test_is_http_exception() -> None:
    """Test that error is an HTTPException."""
    error = OAuth2AuthorizeCallbackError(status_code=400, detail="Error")
    assert isinstance(error, HTTPException)


def test_init_with_route_name() -> None:
    """Test initialization with route_name."""
    mock_client = Mock()
    callback = OAuth2AuthorizeCallback(client=mock_client, route_name="oauth-callback")

    assert callback.client is mock_client
    assert callback.route_name == "oauth-callback"
    assert callback.redirect_url is None


def test_init_with_redirect_url() -> None:
    """Test initialization with redirect_url."""
    mock_client = Mock()
    callback = OAuth2AuthorizeCallback(
        client=mock_client,
        redirect_url="http://localhost:3000/oauth/callback",
    )

    assert callback.client is mock_client
    assert callback.route_name is None
    assert callback.redirect_url == "http://localhost:3000/oauth/callback"


def test_init_requires_either_route_name_or_redirect_url() -> None:
    """Test that either route_name or redirect_url is required."""
    mock_client = Mock()

    with pytest.raises(AssertionError):
        OAuth2AuthorizeCallback(client=mock_client)

    with pytest.raises(AssertionError):
        OAuth2AuthorizeCallback(
            client=mock_client,
            route_name="test",
            redirect_url="http://test.com",
        )


# Note: The OAuth2AuthorizeCallback.__call__ method uses Litestar's Parameter
# decorators for its parameters, which makes direct unit testing complex.
# The callback functionality is better tested via integration tests.


def test_on_app_init() -> None:
    """Test that plugin registers types in signature namespace."""
    plugin = OAuth2ProviderPlugin()

    mock_config = Mock()
    mock_config.signature_namespace = {}

    result = plugin.on_app_init(mock_config)

    assert result is mock_config
    assert "OAuth2AuthorizeCallback" in mock_config.signature_namespace
    assert "AccessTokenState" in mock_config.signature_namespace
    assert "OAuth2Token" in mock_config.signature_namespace
