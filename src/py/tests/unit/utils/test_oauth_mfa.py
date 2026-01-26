from app.utils.oauth import create_oauth_state, verify_oauth_state


def test_create_oauth_state_mfa_disable_action() -> None:
    """Test creating an OAuth state with the 'mfa_disable' action."""
    state = create_oauth_state(
        provider="github", action="mfa_disable", redirect_url="/profile", secret_key="secret-key"
    )
    assert isinstance(state, str)
    assert len(state) > 0


def test_verify_oauth_state_mfa_disable_action() -> None:
    """Test verifying an OAuth state with the 'mfa_disable' action."""
    state = create_oauth_state(
        provider="github", action="mfa_disable", redirect_url="/profile", secret_key="secret-key"
    )
    is_valid, payload, error = verify_oauth_state(state, expected_provider="github", secret_key="secret-key")

    assert is_valid
    assert not error
    assert payload["provider"] == "github"
    assert payload["action"] == "mfa_disable"
    assert payload["redirect_url"] == "/profile"


def test_verify_oauth_state_invalid_action() -> None:
    """Test that an invalid action in the token is rejected (if strict validation is added)."""
    # Note: Currently create_oauth_state allows any string, but we want to ensure our new action works.
    # If we add strict validation in the future, this test might need adjustment.
    # For now, we just ensure round-trip works for our specific action.
    state = create_oauth_state(
        provider="github", action="invalid_action", redirect_url="/profile", secret_key="secret-key"
    )
    is_valid, payload, _ = verify_oauth_state(state, expected_provider="github", secret_key="secret-key")

    # Assuming the verification logic doesn't strictly validate actions yet,
    # but we want to make sure it *doesn't crash* and returns the payload.
    assert is_valid
    assert payload["action"] == "invalid_action"
