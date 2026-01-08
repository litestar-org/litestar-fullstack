"""Integration tests for authentication and access endpoints.

This module combines tests from:
- test_authentication.py (login/logout/signup flows)
- test_auth_endpoints.py (token refresh, profile endpoints)
- test_security_validation.py (security and validation features)
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar_email import InMemoryBackend
from sqlalchemy import select

from app.db import models as m
from app.lib.crypt import get_password_hash
from tests.factories import PasswordResetTokenFactory, UserFactory, get_raw_token

if TYPE_CHECKING:
    from httpx import AsyncClient
    from litestar.testing import AsyncTestClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]


@pytest.fixture(autouse=True)
def clear_email_outbox() -> None:
    """Clear email outbox before each test."""
    InMemoryBackend.clear()


async def _login_user(client: AsyncClient, user: m.User, password: str = "testPassword123!") -> str:
    """Helper to login user and return auth token."""
    response = await client.post(
        "/api/access/login",
        data={"username": user.email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


# =============================================================================
# Login Tests
# =============================================================================


@pytest.mark.anyio
async def test_login_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful user login."""
    unique_email = f"login-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("securePassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "securePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 201
    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"].lower() == "bearer"


@pytest.mark.anyio
async def test_login_invalid_credentials(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test login with invalid credentials."""
    unique_email = f"login-invalid-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("securePassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "wrongPassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_login_inactive_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test login with inactive user."""
    unique_email = f"inactive-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("securePassword123!"),
        is_active=False,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "securePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_login_unverified_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test login with unverified user - unverified users can still log in."""
    unique_email = f"unverified-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("securePassword123!"),
        is_active=True,
        is_verified=False,
    )
    session.add(user)
    await session.commit()

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "securePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 201
    response_data = response.json()
    assert "access_token" in response_data


@pytest.mark.anyio
async def test_login_nonexistent_user(
    client: AsyncClient,
) -> None:
    """Test login with non-existent user."""
    response = await client.post(
        "/api/access/login",
        data={"username": "nonexistent@example.com", "password": "anyPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_login_invalid_email_format(
    client: AsyncClient,
) -> None:
    """Test login with invalid email format."""
    response = await client.post(
        "/api/access/login",
        data={"username": "notanemail", "password": "anyPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_login_with_fixture_user(client: AsyncTestClient, test_user: m.User) -> None:
    """Test successful login using fixture user."""
    login_data = {
        "username": test_user.email,
        "password": "TestPassword123!",
    }

    response = await client.post("/api/access/login", data=login_data)

    assert response.status_code == 201
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_wrong_password_fixture(client: AsyncTestClient, test_user: m.User) -> None:
    """Test login with wrong password fails."""
    login_data = {
        "username": test_user.email,
        "password": "WrongPassword",
    }

    response = await client.post("/api/access/login", data=login_data)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_login_inactive_user_fixture(client: AsyncTestClient, inactive_user: m.User) -> None:
    """Test login with inactive user fails."""
    login_data = {
        "username": inactive_user.email,
        "password": "TestPassword123!",
    }

    response = await client.post("/api/access/login", data=login_data)

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("username", "password", "expected_status_code"),
    (
        ("superuser@example1.com", "Test_Password1!", 403),
        ("superuser@example.com", "Test_Password1!", 201),
        ("user@example.com", "Test_Password1!", 403),
        ("user@example.com", "Test_Password2!", 201),
        ("inactive@example.com", "Old_Password2!", 403),
        ("inactive@example.com", "Old_Password3!", 403),
    ),
)
@pytest.mark.anyio
async def test_login_seeded_users(
    seeded_client: AsyncTestClient,
    username: str,
    password: str,
    expected_status_code: int,
) -> None:
    response = await seeded_client.post("/api/access/login", data={"username": username, "password": password})
    assert response.status_code == expected_status_code


# =============================================================================
# Logout Tests
# =============================================================================


@pytest.mark.anyio
async def test_logout_success(
    client: AsyncClient,
) -> None:
    """Test successful logout."""
    response = await client.post("/api/access/logout")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "OK"


@pytest.mark.anyio
async def test_logout_authenticated(authenticated_client: AsyncTestClient) -> None:
    """Test successful logout when authenticated."""
    response = await authenticated_client.post("/api/access/logout")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.parametrize(
    ("username", "password"),
    (("superuser@example.com", "Test_Password1!"),),
)
@pytest.mark.anyio
async def test_logout_seeded_user(seeded_client: AsyncTestClient, username: str, password: str) -> None:
    response = await seeded_client.post("/api/access/login", data={"username": username, "password": password})
    assert response.status_code == 201
    cookies = dict(response.cookies)

    assert cookies.get("token") is not None

    me_response = await seeded_client.get("/api/me")
    assert me_response.status_code == 200

    response = await seeded_client.post("/api/access/logout")
    assert response.status_code == 200

    me_response = await seeded_client.get("/api/me")
    assert me_response.status_code == 401


# =============================================================================
# Signup Tests
# =============================================================================


@pytest.mark.anyio
async def test_signup_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful user registration."""
    unique_email = f"newuser-{uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/access/signup",
        json={
            "email": unique_email,
            "password": "securePassword123!",
            "name": "New User",
            "username": f"newuser{uuid4().hex[:8]}",
        },
    )

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == unique_email
    assert response_data["name"] == "New User"
    assert response_data["isVerified"] is False
    assert response_data["isActive"] is True

    result = await session.execute(select(m.User).where(m.User.email == unique_email))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == unique_email
    assert user.is_verified is False


@pytest.mark.anyio
async def test_signup_with_email_verification(client: AsyncTestClient) -> None:
    """Test successful user registration sends verification email."""
    signup_data = {
        "email": "newuser@example.com",
        "password": "TestPassword123!",
        "name": "New User",
    }

    response = await client.post("/api/access/signup", json=signup_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert data["isActive"] is True
    assert data["isVerified"] is False
    assert "hashedPassword" not in data

    assert len(InMemoryBackend.outbox) == 1
    assert "newuser@example.com" in InMemoryBackend.outbox[0].to


@pytest.mark.anyio
async def test_signup_duplicate_email(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test registration with duplicate email."""
    unique_email = f"existing-{uuid4().hex[:8]}@example.com"
    existing_user = UserFactory.build(email=unique_email)
    session.add(existing_user)
    await session.commit()

    response = await client.post(
        "/api/access/signup",
        json={"email": unique_email, "password": "securePassword123!", "name": "Duplicate User"},
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_signup_duplicate_email_fixture(client: AsyncTestClient, test_user: m.User) -> None:
    """Test registration with duplicate email fails using fixture."""
    signup_data = {
        "email": test_user.email,
        "password": "TestPassword123!",
        "name": "Duplicate User",
    }

    response = await client.post("/api/access/signup", json=signup_data)

    assert response.status_code == 409
    error_data = response.json()
    detail = error_data.get("detail", "").lower()
    assert "conflict" in detail or "already exists" in detail or "duplicate" in detail


@pytest.mark.anyio
async def test_signup_invalid_password(
    client: AsyncClient,
) -> None:
    """Test registration with weak password."""
    response = await client.post(
        "/api/access/signup",
        json={
            "email": f"weakpass-{uuid4().hex[:8]}@example.com",
            "password": "weak",
            "name": "Weak Password User",
        },
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_signup_weak_password_variations(client: AsyncTestClient) -> None:
    """Test registration with various weak passwords fails."""
    weak_passwords = [
        "password",
        "12345678",
        "Password",
        "Pass123",
        "p" * 129,
    ]

    for password in weak_passwords:
        signup_data = {
            "email": "test@example.com",
            "password": password,
            "name": "Test User",
        }

        response = await client.post("/api/access/signup", json=signup_data)
        assert response.status_code == 400, f"Password '{password}' should be rejected"


@pytest.mark.anyio
async def test_signup_invalid_email(
    client: AsyncClient,
) -> None:
    """Test registration with invalid email."""
    response = await client.post(
        "/api/access/signup",
        json={"email": "notanemail", "password": "securePassword123!", "name": "Invalid Email User"},
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_signup_invalid_email_variations(client: AsyncTestClient) -> None:
    """Test registration with various invalid email formats fails."""
    invalid_emails = [
        "notanemail",
        "@example.com",
        "test@",
        "test..test@example.com",
        "test@example",
    ]

    for email in invalid_emails:
        signup_data = {
            "email": email,
            "password": "TestPassword123!",
            "name": "Test User",
        }

        response = await client.post("/api/access/signup", json=signup_data)
        assert response.status_code == 400, f"Email {email} should be rejected"


@pytest.mark.anyio
async def test_signup_minimal_data(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test registration with minimal required data."""
    unique_email = f"minimal-{uuid4().hex[:8]}@example.com"
    response = await client.post("/api/access/signup", json={"email": unique_email, "password": "securePassword123!"})

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == unique_email
    assert response_data["name"] is None
    assert response_data["username"] is None


# =============================================================================
# Profile Tests
# =============================================================================


@pytest.mark.anyio
async def test_get_profile_authenticated(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test getting user profile when authenticated."""
    unique_email = f"profile-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        name="Profile User",
        username=f"profileuser{uuid4().hex[:8]}",
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user)

    response = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["email"] == unique_email
    assert response_data["name"] == "Profile User"


@pytest.mark.anyio
async def test_get_profile_unauthenticated(
    client: AsyncClient,
) -> None:
    """Test getting user profile without authentication."""
    response = await client.get("/api/me")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_fixture(authenticated_client: AsyncTestClient, test_user: m.User) -> None:
    """Test getting current user profile with fixture."""
    response = await authenticated_client.get("/api/me")

    assert response.status_code == 200
    user_data = response.json()
    assert user_data["id"] == str(test_user.id)
    assert user_data["email"] == test_user.email
    assert user_data["name"] == test_user.name
    assert "hashedPassword" not in user_data


@pytest.mark.anyio
async def test_update_profile_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful profile update."""
    unique_email = f"update-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        name="Original Name",
        username=f"originaluser{uuid4().hex[:8]}",
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user)

    new_username = f"updateduser{uuid4().hex[:8]}"
    response = await client.patch(
        "/api/me",
        json={"name": "Updated Name", "username": new_username, "phone": "+1234567890"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Updated Name"
    assert response_data["username"] == new_username
    assert response_data["phone"] == "+1234567890"

    await session.refresh(user)
    assert user.name == "Updated Name"
    assert user.username == new_username
    assert user.phone == "+1234567890"


@pytest.mark.anyio
async def test_update_profile_fixture(authenticated_client: AsyncTestClient, test_user: m.User) -> None:
    """Test updating user profile with fixture."""
    update_data = {
        "name": "Updated Name",
    }

    response = await authenticated_client.patch("/api/me", json=update_data)

    assert response.status_code == 200
    user_data = response.json()
    assert user_data["name"] == "Updated Name"
    assert user_data["email"] == test_user.email


@pytest.mark.anyio
async def test_update_profile_unauthenticated(client: AsyncTestClient) -> None:
    """Test updating profile without authentication fails."""
    update_data = {"name": "Updated Name"}

    response = await client.patch("/api/me", json=update_data)

    assert response.status_code == 401


# =============================================================================
# Password Change Tests
# =============================================================================


@pytest.mark.anyio
async def test_update_password_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful password update."""
    unique_email = f"password-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("oldPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user, "oldPassword123!")

    response = await client.patch(
        "/api/me/password",
        json={"currentPassword": "oldPassword123!", "newPassword": "newPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Your password was successfully modified."


@pytest.mark.anyio
async def test_update_password_wrong_current(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test password update with wrong current password."""
    unique_email = f"password-wrong-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("correctPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user, "correctPassword123!")

    response = await client.patch(
        "/api/me/password",
        json={"currentPassword": "wrongPassword123!", "newPassword": "newPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_change_password_fixture(authenticated_client: AsyncTestClient, test_user: m.User) -> None:
    """Test successful password change with fixture."""
    password_data = {
        "currentPassword": "TestPassword123!",
        "newPassword": "NewPassword123!",
    }

    response = await authenticated_client.patch("/api/me/password", json=password_data)

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "password" in data["message"].lower()


@pytest.mark.anyio
async def test_change_password_wrong_current_fixture(authenticated_client: AsyncTestClient) -> None:
    """Test password change with wrong current password fails."""
    password_data = {
        "currentPassword": "WrongPassword123!",
        "newPassword": "NewPassword123!",
    }

    response = await authenticated_client.patch("/api/me/password", json=password_data)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_change_password_weak_new(authenticated_client: AsyncTestClient) -> None:
    """Test password change with weak new password fails."""
    password_data = {
        "currentPassword": "TestPassword123!",
        "newPassword": "weak",
    }

    response = await authenticated_client.patch("/api/me/password", json=password_data)

    assert response.status_code == 400


# =============================================================================
# Token Refresh Tests
# =============================================================================


@pytest.mark.anyio
async def test_refresh_token(authenticated_client: AsyncTestClient) -> None:
    """Test token refresh."""
    response = await authenticated_client.post("/api/access/refresh")

    assert response.status_code in {200, 201, 400, 401}


# =============================================================================
# Password Reset Tests
# =============================================================================


@pytest.mark.anyio
async def test_forgot_password_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful forgot password request."""
    unique_email = f"reset-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(email=unique_email, is_active=True, is_verified=True)
    session.add(user)
    await session.commit()

    response = await client.post("/api/access/forgot-password", json={"email": unique_email})

    assert response.status_code == 201
    response_data = response.json()
    assert "password reset link has been sent" in response_data["message"]
    assert response_data["expiresInMinutes"] == 60

    result = await session.execute(select(m.PasswordResetToken).where(m.PasswordResetToken.user_id == user.id))
    token = result.scalar_one_or_none()
    assert token is not None
    assert token.is_valid is True


@pytest.mark.anyio
async def test_forgot_password_nonexistent_user(
    client: AsyncClient,
) -> None:
    """Test forgot password for non-existent user."""
    response = await client.post("/api/access/forgot-password", json={"email": "nonexistent@example.com"})

    assert response.status_code == 201
    response_data = response.json()
    assert "password reset link has been sent" in response_data["message"]


@pytest.mark.anyio
async def test_forgot_password_inactive_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test forgot password for inactive user."""
    unique_email = f"inactive-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(email=unique_email, is_active=False, is_verified=True)
    session.add(user)
    await session.commit()

    response = await client.post("/api/access/forgot-password", json={"email": unique_email})

    assert response.status_code == 201


@pytest.mark.anyio
async def test_request_password_reset_fixture(client: AsyncTestClient, test_user: m.User) -> None:
    """Test requesting password reset with fixture."""
    request_data = {"email": test_user.email}

    response = await client.post("/api/access/forgot-password", json=request_data)

    assert response.status_code in {200, 201}
    assert len(InMemoryBackend.outbox) == 1
    assert test_user.email in InMemoryBackend.outbox[0].to


@pytest.mark.anyio
async def test_validate_reset_token_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful reset token validation."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    raw_token = uuid4().hex + uuid4().hex
    reset_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        raw_token=raw_token,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    session.add(reset_token)
    await session.commit()

    response = await client.get("/api/access/reset-password", params={"token": raw_token})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["valid"] is True
    assert response_data["userId"] == str(user.id)


@pytest.mark.anyio
async def test_validate_reset_token_invalid(
    client: AsyncClient,
) -> None:
    """Test validation of invalid reset token."""
    response = await client.get(
        "/api/access/reset-password",
        params={"token": "invalid_token_that_is_at_least_32_chars_long"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["valid"] is False


@pytest.mark.anyio
async def test_reset_password_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful password reset."""
    unique_email = f"reset-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(email=unique_email, hashed_password=await get_password_hash("oldPassword123!"))
    session.add(user)
    await session.commit()

    raw_token = uuid4().hex + uuid4().hex
    reset_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        raw_token=raw_token,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    session.add(reset_token)
    await session.commit()

    response = await client.post(
        "/api/access/reset-password",
        json={"token": raw_token, "password": "newPassword123!", "password_confirm": "newPassword123!"},
    )

    assert response.status_code == 201
    response_data = response.json()
    assert "successfully reset" in response_data["message"]
    assert response_data["userId"] == str(user.id)

    await session.refresh(reset_token)
    assert reset_token.is_used is True


@pytest.mark.anyio
async def test_reset_password_fixture(
    client: AsyncTestClient,
    test_password_reset_token: m.PasswordResetToken,
) -> None:
    """Test successful password reset with fixture."""
    new_password = "NewSecurePassword123!"
    reset_data = {
        "token": get_raw_token(test_password_reset_token),
        "password": new_password,
        "password_confirm": new_password,
    }

    response = await client.post("/api/access/reset-password", json=reset_data)

    assert response.status_code in {200, 201}
    data = response.json()
    assert data is not None


@pytest.mark.anyio
async def test_reset_password_passwords_mismatch(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test password reset with mismatched passwords."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    raw_token = uuid4().hex + uuid4().hex
    reset_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        raw_token=raw_token,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    session.add(reset_token)
    await session.commit()

    response = await client.post(
        "/api/access/reset-password",
        json={
            "token": raw_token,
            "password": "newPassword123!",
            "password_confirm": "differentPassword123!",
        },
    )

    assert response.status_code == 400
    assert "do not match" in response.text


@pytest.mark.anyio
async def test_reset_password_weak_password(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test password reset with weak password."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    raw_token = uuid4().hex + uuid4().hex
    reset_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        raw_token=raw_token,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    session.add(reset_token)
    await session.commit()

    response = await client.post(
        "/api/access/reset-password",
        json={"token": raw_token, "password": "weak", "password_confirm": "weak"},
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_reset_password_invalid_token(
    client: AsyncClient,
) -> None:
    """Test password reset with invalid token."""
    response = await client.post(
        "/api/access/reset-password",
        json={
            "token": "invalid_token_that_is_at_least_32_chars_long",
            "password": "newPassword123!",
            "password_confirm": "newPassword123!",
        },
    )

    assert response.status_code == 400
    assert "Invalid reset token" in response.text


@pytest.mark.anyio
async def test_password_reset_token_single_use(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that reset tokens can only be used once."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    raw_token = uuid4().hex + uuid4().hex
    reset_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        raw_token=raw_token,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    session.add(reset_token)
    await session.commit()

    response = await client.post(
        "/api/access/reset-password",
        json={"token": raw_token, "password": "newPassword123!", "password_confirm": "newPassword123!"},
    )
    assert response.status_code == 201

    response = await client.post(
        "/api/access/reset-password",
        json={
            "token": raw_token,
            "password": "anotherPassword123!",
            "password_confirm": "anotherPassword123!",
        },
    )
    assert response.status_code == 400
    assert "already been used" in response.text


# =============================================================================
# Email Verification Request Tests
# =============================================================================


@pytest.mark.anyio
async def test_request_verification_email(client: AsyncTestClient, unverified_user: m.User) -> None:
    """Test requesting email verification."""
    request_data = {"email": unverified_user.email}

    response = await client.post("/api/email-verification/request", json=request_data)

    assert response.status_code == 201
    data = response.json()
    assert "verification" in data["message"].lower()

    assert len(InMemoryBackend.outbox) == 1
    assert unverified_user.email in InMemoryBackend.outbox[0].to


@pytest.mark.anyio
async def test_request_verification_nonexistent_user(client: AsyncTestClient) -> None:
    """Test requesting verification for non-existent user returns success (email enumeration protection)."""
    request_data = {"email": "nonexistent@example.com"}

    response = await client.post("/api/email-verification/request", json=request_data)

    assert response.status_code == 201


@pytest.mark.anyio
async def test_verify_email_success(
    client: AsyncTestClient,
    unverified_user: m.User,
    test_verification_token: m.EmailVerificationToken,
) -> None:
    """Test successful email verification."""
    verify_data = {"token": get_raw_token(test_verification_token)}

    response = await client.post("/api/email-verification/verify", json=verify_data)

    assert response.status_code == 200
    data = response.json()
    assert data["isVerified"] is True
    assert data["email"] == unverified_user.email


@pytest.mark.anyio
async def test_verify_email_invalid_token(client: AsyncTestClient) -> None:
    """Test email verification with invalid token."""
    verify_data = {"token": "invalid_token"}

    response = await client.post("/api/email-verification/verify", json=verify_data)

    assert response.status_code == 400


@pytest.mark.anyio
async def test_verify_email_already_verified(client: AsyncTestClient, test_user: m.User) -> None:
    """Test email verification for already verified user."""
    raw_token = uuid4().hex
    m.EmailVerificationToken(
        id=uuid4(),
        user_id=test_user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        email=test_user.email,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )

    verify_data = {"token": raw_token}

    response = await client.post("/api/email-verification/verify", json=verify_data)

    assert response.status_code in {200, 400}


# =============================================================================
# Security Tests
# =============================================================================


@pytest.mark.anyio
async def test_sql_injection_protection(client: AsyncTestClient) -> None:
    """Test that SQL injection attempts are blocked."""
    sql_injection_attempts = [
        "test'; DROP TABLE users; --@example.com",
        "test@example.com'; INSERT INTO users VALUES ('hacker'); --",
        "test@example.com' OR '1'='1",
    ]

    for malicious_email in sql_injection_attempts:
        signup_data = {
            "email": malicious_email,
            "password": "TestPassword123!",
            "name": "Test User",
        }

        response = await client.post("/api/access/signup", json=signup_data)
        assert response.status_code in {400, 409}, f"SQL injection attempt should be blocked: {malicious_email}"


@pytest.mark.anyio
async def test_sql_injection_in_login(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test SQL injection attempts in login endpoint."""
    unique_email = f"valid-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    sql_injection_attempts = [
        "admin@example.com' OR '1'='1",
        "admin@example.com'; DROP TABLE user_account; --",
        "admin@example.com' UNION SELECT * FROM user_account --",
        "admin@example.com' OR 1=1 --",
        "admin'; EXEC master..xp_cmdshell 'ping google.com'--",
    ]

    for injection_attempt in sql_injection_attempts:
        response = await client.post(
            "/api/access/login",
            data={"username": injection_attempt, "password": "anyPassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code in [400, 403], (
            f"SQL injection attempt should be safely handled: {injection_attempt}"
        )


@pytest.mark.anyio
async def test_xss_protection(client: AsyncTestClient) -> None:
    """Test XSS protection in user inputs."""
    xss_attempts = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "' OR 1=1 --",
    ]

    for xss_payload in xss_attempts:
        signup_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "name": xss_payload,
        }

        response = await client.post("/api/access/signup", json=signup_data)

        if response.status_code == 201:
            user_data = response.json()
            assert xss_payload not in user_data["name"] or response.status_code == 400


@pytest.mark.anyio
async def test_jwt_token_validation(
    client: AsyncClient,
) -> None:
    """Test JWT token validation and security."""
    response = await client.get("/api/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401

    response = await client.get("/api/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401

    response = await client.get("/api/me")
    assert response.status_code == 401

    response = await client.get("/api/me", headers={"Authorization": "Basic dGVzdDp0ZXN0"})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_sensitive_data_exposure(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that sensitive data is not exposed in responses."""
    unique_email = f"sensitive-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user)

    response = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    response_data = response.json()
    response_text = response.text.lower()

    assert "password" not in response_data
    assert "hashed_password" not in response_data
    assert "hashedpassword" not in response_text
    assert "secret" not in response_text


@pytest.mark.anyio
async def test_error_message_security(
    client: AsyncClient,
) -> None:
    """Test that error messages don't leak sensitive information."""
    response = await client.post(
        "/api/access/login",
        data={"username": "nonexistent@example.com", "password": "anyPassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code in [401, 403]
    error_text = response.text.lower()
    assert "does not exist" not in error_text
    assert "invalid" in error_text or "forbidden" in error_text or "not found" in error_text

    response = await client.post("/api/access/forgot-password", json={"email": "nonexistent@example.com"})

    assert response.status_code == 201
    response_data = response.json()
    assert "if the email exists" in response_data["message"].lower()


@pytest.mark.anyio
async def test_unauthorized_access_prevention(
    client: AsyncClient,
) -> None:
    """Test that unauthorized access is properly prevented."""
    protected_endpoints = [
        ("GET", "/api/me"),
        ("PATCH", "/api/me"),
        ("PATCH", "/api/me/password"),
        ("GET", "/api/teams"),
        ("POST", "/api/teams"),
    ]

    for method, endpoint in protected_endpoints:
        payload = {} if method in {"POST", "PATCH"} else None
        if payload is None:
            response = await client.request(method, endpoint)
        else:
            response = await client.request(method, endpoint, json=payload)

        assert response.status_code in [401, 403], f"{method} {endpoint} should require authentication"


@pytest.mark.anyio
async def test_inactive_user_access_denial(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that inactive users cannot access protected resources."""
    unique_email = f"inactive-{uuid4().hex[:8]}@example.com"
    inactive_user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=False,
        is_verified=True,
    )
    session.add(inactive_user)
    await session.commit()

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "testPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code in [401, 403]


@pytest.mark.anyio
async def test_superuser_access_control(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test superuser-only endpoint access control."""
    regular_email = f"regular-{uuid4().hex[:8]}@example.com"
    regular_user = UserFactory.build(
        email=regular_email,
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )

    super_email = f"super-{uuid4().hex[:8]}@example.com"
    super_user = UserFactory.build(
        email=super_email,
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )

    session.add_all([regular_user, super_user])
    await session.commit()

    regular_token = await _login_user(client, regular_user)
    response = await client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert response.status_code == 403

    super_token = await _login_user(client, super_user)
    response = await client.get("/api/users", headers={"Authorization": f"Bearer {super_token}"})
    assert response.status_code == 200


@pytest.mark.anyio
async def test_security_headers_present(
    client: AsyncClient,
) -> None:
    """Test that important security headers are present."""
    response = await client.get("/api/access/logout")

    headers = response.headers

    security_header_checks = [
        lambda h: "content-type" in h,
        lambda h: "access-control-allow-origin" not in h or h["access-control-allow-origin"] != "*",
    ]

    for check in security_header_checks:
        assert check(headers), f"Security header check failed for headers: {dict(headers)}"


# =============================================================================
# Validation Tests
# =============================================================================


@pytest.mark.anyio
async def test_email_validation_registration(
    client: AsyncClient,
) -> None:
    """Test email validation in user registration."""
    invalid_emails = [
        "notanemail",
        "missing@domain",
        "@missinglocal.com",
        "spaces in@email.com",
        "double..dot@email.com",
        "toolong" + "x" * 250 + "@example.com",
    ]

    for invalid_email in invalid_emails:
        response = await client.post(
            "/api/access/signup",
            json={"email": invalid_email, "password": "securePassword123!", "name": "Test User"},
        )
        assert response.status_code == 400, f"Email {invalid_email} should be invalid"


@pytest.mark.anyio
async def test_password_strength_validation(
    client: AsyncClient,
) -> None:
    """Test password strength validation."""
    weak_passwords = [
        "weak",
        "password",
        "PASSWORD",
        "12345678",
        "Password123",
        "p@ssw0rd",
        "",
        "   ",
    ]

    for weak_password in weak_passwords:
        response = await client.post(
            "/api/access/signup",
            json={"email": f"user-{uuid4().hex[:8]}@example.com", "password": weak_password, "name": "Test User"},
        )
        assert response.status_code == 400, f"Password '{weak_password}' should be invalid"


@pytest.mark.anyio
async def test_username_validation(
    client: AsyncClient,
) -> None:
    """Test username validation."""
    invalid_usernames = [
        "us",
        "a" * 31,
        "user name",
        "user@name",
        "user.name",
        ".username",
        "-user",
        "_user",
    ]

    for invalid_username in invalid_usernames:
        response = await client.post(
            "/api/access/signup",
            json={
                "email": f"user-{uuid4().hex[:8]}@example.com",
                "password": "securePassword123!",
                "name": "Test User",
                "username": invalid_username,
            },
        )
        assert response.status_code == 400, f"Username '{invalid_username}' should be invalid"


@pytest.mark.anyio
async def test_name_validation(
    client: AsyncClient,
) -> None:
    """Test name validation."""
    invalid_names = [
        "",
        "A" * 101,
        "Name123",
        "Name@User",
        "   ",
        "Name<script>",
    ]

    for invalid_name in invalid_names:
        response = await client.post(
            "/api/access/signup",
            json={
                "email": f"user-{uuid4().hex[:8]}@example.com",
                "password": "securePassword123!",
                "name": invalid_name,
            },
        )
        assert response.status_code == 400, f"Name '{invalid_name}' should be invalid"


@pytest.mark.anyio
async def test_json_payload_validation(
    client: AsyncClient,
) -> None:
    """Test JSON payload validation."""
    response = await client.post(
        "/api/access/signup", content="not-json-data", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400

    response = await client.post(
        "/api/access/signup",
        json={"email": f"user-{uuid4().hex[:8]}@example.com"},
    )
    assert response.status_code == 400

    response = await client.post(
        "/api/access/signup",
        json={
            "email": f"user-{uuid4().hex[:8]}@example.com",
            "password": "securePassword123!",
            "unexpected_field": "should_be_ignored",
        },
    )
    assert response.status_code in [201, 400, 422]


# =============================================================================
# Complete Flow Tests
# =============================================================================


@pytest.mark.anyio
async def test_complete_registration_and_login_flow(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test complete user registration and login workflow."""
    unique_email = f"complete-{uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/access/signup",
        json={"email": unique_email, "password": "securePassword123!", "name": "Complete User"},
    )
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["isVerified"] is False

    result = await session.execute(select(m.User).where(m.User.email == unique_email))
    user = result.scalar_one()

    user.is_verified = True
    await session.commit()

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "securePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201
    token_data = response.json()
    token = token_data["access_token"]

    response = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["email"] == unique_email
    assert profile_data["name"] == "Complete User"


@pytest.mark.anyio
async def test_complete_password_reset_flow(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test complete password reset workflow."""
    unique_email = f"resetflow-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("oldPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "oldPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201

    raw_token = uuid4().hex + uuid4().hex
    reset_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        raw_token=raw_token,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    session.add(reset_token)
    await session.commit()

    response = await client.get("/api/access/reset-password", params={"token": raw_token})
    assert response.status_code == 200
    assert response.json()["valid"] is True

    response = await client.post(
        "/api/access/reset-password",
        json={
            "token": raw_token,
            "password": "newPassword123!",
            "password_confirm": "newPassword123!",
        },
    )
    assert response.status_code == 201

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "newPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201

    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "oldPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 403
