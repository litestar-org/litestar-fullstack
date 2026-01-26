import time
from unittest.mock import MagicMock

import jwt

from app.utils.oauth import OAuth2ProviderPlugin, build_oauth_error_redirect, create_oauth_state, verify_oauth_state

SECRET = "test-secret"


def test_oauth_state_cycle() -> None:
    state = create_oauth_state("google", "http://localhost/cb", SECRET, action="login", user_id="123")
    is_valid, payload, error = verify_oauth_state(state, "google", SECRET)

    assert is_valid is True
    assert payload["provider"] == "google"
    assert payload["action"] == "login"
    assert payload["user_id"] == "123"
    assert not error


def test_verify_oauth_state_invalid_provider() -> None:
    state = create_oauth_state("google", "http://localhost/cb", SECRET)
    is_valid, _, error = verify_oauth_state(state, "github", SECRET)
    assert is_valid is False
    assert error == "Invalid OAuth provider"


def test_verify_oauth_state_expired() -> None:
    payload = {"provider": "google", "exp": int(time.time()) - 100}
    state = jwt.encode(payload, SECRET, algorithm="HS256")
    is_valid, payload, error = verify_oauth_state(state, "google", SECRET)
    assert is_valid is False
    assert error == "OAuth session expired"


def test_verify_oauth_state_invalid_token() -> None:
    is_valid, _, error = verify_oauth_state("invalid", "google", SECRET)
    assert is_valid is False
    assert error == "Invalid OAuth state"


def test_build_oauth_error_redirect() -> None:
    url = build_oauth_error_redirect("http://localhost", "access_denied", "User said no")
    assert "error=access_denied" in url
    assert "message=User+said+no" in url
    assert url.startswith("http://localhost?")

    url2 = build_oauth_error_redirect("http://localhost?existing=1", "err", "msg")
    assert "&error=err" in url2


def test_oauth_provider_plugin() -> None:
    plugin = OAuth2ProviderPlugin()
    app_config = MagicMock()
    app_config.signature_namespace = {}

    result = plugin.on_app_init(app_config)
    assert "OAuth2AuthorizeCallback" in app_config.signature_namespace
    assert result == app_config
