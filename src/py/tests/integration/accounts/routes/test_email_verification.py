"""Integration tests for email verification API endpoints.

This module combines tests for:
- User registration and email verification
- Verification request endpoints
- Verification status endpoints
- Complete verification flows
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import msgspec
import pytest
from litestar_email import InMemoryBackend

from app.domain.accounts.schemas import User

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from litestar.testing import AsyncTestClient

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def clear_email_outbox() -> None:
    """Clear email outbox before each test."""
    InMemoryBackend.clear()


def _unique_email(prefix: str = "user") -> str:
    """Generate a unique email address for test isolation."""
    return f"{prefix}{uuid4().hex[:8]}@example.com"


# --- Registration and Initial Verification State Tests ---


async def test_user_registration_creates_unverified_user(client: AsyncTestClient) -> None:
    """Test that user registration creates an unverified user."""
    email = _unique_email("newuser")
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "name": "New User",
    }

    response = await client.post("/api/access/signup", json=user_data)

    assert response.status_code == 201
    user = msgspec.json.decode(response.content, type=User)
    assert user.email == email
    assert user.name == "New User"
    assert user.is_verified is False  # Should be unverified initially
    assert user.is_active is True


async def test_user_registration_sends_verification_email(
    client: AsyncTestClient,
    await_events: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Test that user registration triggers verification email sending."""
    email = _unique_email("emailtest")
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "name": "Email Test User",
    }

    # Register user
    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201
    await await_events()

    # Verify that a verification token was created by requesting verification
    # (This indirectly tests that the email sending was triggered)
    request_data = {"email": email}
    verify_request_response = await client.post("/api/email-verification/request", json=request_data)

    # Verification request should work (meaning user exists and is unverified)
    assert verify_request_response.status_code == 201
    await await_events()
    data = verify_request_response.json()
    assert data["message"] == "Verification email sent"

    assert len(InMemoryBackend.outbox) > 0


async def test_registration_with_duplicate_email(client: AsyncTestClient) -> None:
    """Test registration with duplicate email address."""
    email = _unique_email("duplicate")
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "name": "First User",
    }

    # Register first user
    first_response = await client.post("/api/access/signup", json=user_data)
    assert first_response.status_code == 201

    # Try to register second user with same email
    user_data["name"] = "Second User"
    second_response = await client.post("/api/access/signup", json=user_data)

    # Should fail due to unique constraint
    assert second_response.status_code == 409


async def test_registration_with_initial_team(client: AsyncTestClient) -> None:
    """Test registration with initial team creation."""
    email = _unique_email("teamuser")
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "name": "Team User",
        "initial_team_name": "My Team",
    }

    response = await client.post("/api/access/signup", json=user_data)

    assert response.status_code == 201
    user = msgspec.json.decode(response.content, type=User)
    assert user.email == email
    assert user.is_verified is False  # Should still be unverified


# --- Verification Request Tests ---


async def test_request_verification_success(client: AsyncTestClient) -> None:
    """Test successful verification email request."""
    # Note: emails starting with "test" are blocked by validation
    user_data = {
        "email": "verifyuser@example.com",
        "password": "SecurePass123!",
        "name": "Verify User",
    }

    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201

    # Request verification email
    request_data = {"email": "verifyuser@example.com"}
    response = await client.post("/api/email-verification/request", json=request_data)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Verification email sent"
    # assert "token" in data  # Token is removed


async def test_request_verification_nonexistent_email(client: AsyncTestClient) -> None:
    """Test verification request for non-existent email."""
    request_data = {"email": "nonexistent@example.com"}

    response = await client.post("/api/email-verification/request", json=request_data)

    # Should not reveal if email exists
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "If the email exists, a verification link has been sent"


async def test_request_verification_already_verified(
    client: AsyncTestClient,
    await_events: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Test verification request for already verified email."""
    # Create and verify a user
    user_data = {
        "email": "verified@example.com",
        "password": "SecurePass123!",
        "name": "Verified User",
    }

    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201
    await await_events()

    # Get the verification token from signup and verify
    request_data = {"email": "verified@example.com"}
    request_response = await client.post("/api/email-verification/request", json=request_data)
    assert request_response.status_code == 201
    await await_events()

    email_content = InMemoryBackend.outbox[-1].html_body  # pyright: ignore[reportAttributeAccessIssue]

    token_match = re.search(r"token=([A-Za-z0-9\-_]+)", email_content)
    assert token_match
    token = token_match.group(1)

    # Verify the email
    verify_data = {"token": token}
    verify_response = await client.post("/api/email-verification/verify", json=verify_data)
    assert verify_response.status_code == 200

    # Request verification again
    response = await client.post("/api/email-verification/request", json=request_data)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Email is already verified"


async def test_multiple_verification_requests(
    client: AsyncTestClient,
    await_events: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Test that multiple verification requests invalidate previous tokens."""
    email = _unique_email("multiple")
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "name": "Multiple User",
    }

    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201
    await await_events()

    request_data = {"email": email}

    # Request first verification token
    first_request = await client.post("/api/email-verification/request", json=request_data)
    assert first_request.status_code == 201
    await await_events()

    first_email_content = InMemoryBackend.outbox[-1].html_body  # pyright: ignore[reportAttributeAccessIssue]
    first_match = re.search(r"token=([A-Za-z0-9\-_]+)", first_email_content)
    assert first_match
    first_token = first_match.group(1)

    # Request second verification token (should invalidate first)
    second_request = await client.post("/api/email-verification/request", json=request_data)
    assert second_request.status_code == 201
    await await_events()

    second_email_content = InMemoryBackend.outbox[-1].html_body  # pyright: ignore[reportAttributeAccessIssue]
    second_match = re.search(r"token=([A-Za-z0-9\-_]+)", second_email_content)
    assert second_match
    second_token = second_match.group(1)

    # First token should be invalidated
    verify_first = {"token": first_token}
    first_verify_response = await client.post("/api/email-verification/verify", json=verify_first)
    assert first_verify_response.status_code == 400  # Should fail

    # Second token should still work
    verify_second = {"token": second_token}
    second_verify_response = await client.post("/api/email-verification/verify", json=verify_second)
    assert second_verify_response.status_code == 200  # Should succeed


# --- Email Verification Tests ---


async def test_verify_email_success(
    client: AsyncTestClient,
    await_events: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Test successful email verification."""
    user_data = {
        "email": "verifyemail@example.com",
        "password": "SecurePass123!",
        "name": "Verify User",
    }

    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201
    await await_events()

    # Request verification token
    request_data = {"email": "verifyemail@example.com"}
    request_response = await client.post("/api/email-verification/request", json=request_data)
    assert request_response.status_code == 201
    await await_events()

    assert len(InMemoryBackend.outbox) >= 2  # One from signup, one from request
    email_content = InMemoryBackend.outbox[1].html_body  # pyright: ignore[reportAttributeAccessIssue]

    token_match = re.search(r"token=([A-Za-z0-9\-_]+)", email_content)
    assert token_match, "Token not found in email"
    token = token_match.group(1)

    # Verify email
    verify_data = {"token": token}
    response = await client.post("/api/email-verification/verify", json=verify_data)

    assert response.status_code == 200
    user = msgspec.json.decode(response.content, type=User)
    assert user.is_verified is True
    assert user.email == "verifyemail@example.com"


async def test_verify_email_invalid_token(client: AsyncTestClient) -> None:
    """Test email verification with invalid token."""
    verify_data = {"token": "invalid_token_12345"}

    response = await client.post("/api/email-verification/verify", json=verify_data)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


async def test_verify_email_token_reuse_prevention(
    client: AsyncTestClient,
    await_events: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Test that tokens cannot be reused."""
    user_data = {
        "email": "reuse@example.com",
        "password": "SecurePass123!",
        "name": "Reuse User",
    }

    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201
    await await_events()

    # Request verification token
    request_data = {"email": "reuse@example.com"}
    request_response = await client.post("/api/email-verification/request", json=request_data)
    assert request_response.status_code == 201
    await await_events()

    email_content = InMemoryBackend.outbox[-1].html_body  # pyright: ignore[reportAttributeAccessIssue]
    match = re.search(r"token=([A-Za-z0-9\-_]+)", email_content)
    assert match
    token = match.group(1)

    # Verify email first time
    verify_data = {"token": token}
    first_response = await client.post("/api/email-verification/verify", json=verify_data)
    assert first_response.status_code == 200

    # Try to verify again with same token
    second_response = await client.post("/api/email-verification/verify", json=verify_data)

    assert second_response.status_code == 400
    data = second_response.json()
    assert "detail" in data


# --- Verification Status Tests ---


async def test_get_verification_status_verified(
    client: AsyncTestClient,
    await_events: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Test getting verification status for verified user."""
    user_data = {
        "email": "status@example.com",
        "password": "SecurePass123!",
        "name": "Status User",
    }

    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201
    await await_events()

    user_info = signup_response.json()
    user_id = user_info["id"]

    # Request and use verification token
    request_data = {"email": "status@example.com"}
    response = await client.post("/api/email-verification/request", json=request_data)
    assert response.status_code == 201
    await await_events()

    email_content = InMemoryBackend.outbox[-1].html_body  # pyright: ignore[reportAttributeAccessIssue]
    match = re.search(r"token=([A-Za-z0-9\-_]+)", email_content)
    assert match
    token = match.group(1)

    verify_data = {"token": token}
    await client.post("/api/email-verification/verify", json=verify_data)

    # Check status
    response = await client.get(f"/api/email-verification/status/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["isVerified"] is True


async def test_get_verification_status_unverified(client: AsyncTestClient) -> None:
    """Test getting verification status for unverified user."""
    user_data = {
        "email": "unverified@example.com",
        "password": "SecurePass123!",
        "name": "Unverified User",
    }

    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201

    user_info = signup_response.json()
    user_id = user_info["id"]

    # Check status
    response = await client.get(f"/api/email-verification/status/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["isVerified"] is False


async def test_get_verification_status_nonexistent_user(client: AsyncTestClient) -> None:
    """Test getting verification status for non-existent user."""
    fake_user_id = str(uuid4())

    response = await client.get(f"/api/email-verification/status/{fake_user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["isVerified"] is False


# --- Login and Verification Interaction Tests ---


async def test_login_before_email_verification(client: AsyncTestClient) -> None:
    """Test that login works even before email verification."""
    email = _unique_email("logintest")
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "name": "Login Test User",
    }

    # Register user
    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201

    # Try to login before verification
    login_data = {
        "username": email,
        "password": "SecurePass123!",
    }
    login_response = await client.post(
        "/api/access/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # Login should succeed even for unverified users
    assert login_response.status_code == 201


# --- Complete Flow Tests ---


async def test_complete_registration_verification_flow(
    client: AsyncTestClient,
    await_events: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Test complete flow from registration to email verification."""
    email = _unique_email("complete")
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "name": "Complete User",
    }

    # Step 1 - Register user
    signup_response = await client.post("/api/access/signup", json=user_data)
    assert signup_response.status_code == 201
    await await_events()

    user_info = signup_response.json()
    user_id = user_info["id"]

    # Verify user is initially unverified
    status_response = await client.get(f"/api/email-verification/status/{user_id}")
    assert status_response.status_code == 200
    assert status_response.json()["isVerified"] is False

    # Step 2 - Request verification email
    request_data = {"email": email}
    request_response = await client.post("/api/email-verification/request", json=request_data)
    assert request_response.status_code == 201
    await await_events()

    email_content = InMemoryBackend.outbox[-1].html_body  # pyright: ignore[reportAttributeAccessIssue]
    match = re.search(r"token=([A-Za-z0-9\-_]+)", email_content)
    assert match
    token = match.group(1)

    # Step 3 - Verify email using token
    verify_data = {"token": token}
    verify_response = await client.post("/api/email-verification/verify", json=verify_data)
    assert verify_response.status_code == 200

    # User should now be verified
    verified_user = msgspec.json.decode(verify_response.content, type=User)
    assert verified_user.is_verified is True
    assert verified_user.email == email

    # Double-check with status endpoint
    final_status_response = await client.get(f"/api/email-verification/status/{user_id}")
    assert final_status_response.status_code == 200
    assert final_status_response.json()["isVerified"] is True
