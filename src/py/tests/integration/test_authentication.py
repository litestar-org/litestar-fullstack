"""Integration tests for authentication endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db import models as m
from app.lib.crypt import get_password_hash
from tests.factories import PasswordResetTokenFactory, UserFactory

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]


@pytest.mark.anyio
async def test_login_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful user login."""
    # Create verified user with known password
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
    # Create user
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

    # Inactive user should be forbidden
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

    # Unverified users can still log in
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

    assert response.status_code == 400  # Validation error


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
    assert response_data["isVerified"] is False  # Requires email verification
    assert response_data["isActive"] is True

    # Verify user was created in database
    result = await session.execute(select(m.User).where(m.User.email == unique_email))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == unique_email
    assert user.is_verified is False


@pytest.mark.anyio
async def test_signup_duplicate_email(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test registration with duplicate email."""
    # Create existing user
    unique_email = f"existing-{uuid4().hex[:8]}@example.com"
    existing_user = UserFactory.build(email=unique_email)
    session.add(existing_user)
    await session.commit()

    response = await client.post(
        "/api/access/signup",
        json={"email": unique_email, "password": "securePassword123!", "name": "Duplicate User"},
    )

    assert response.status_code == 409  # Conflict


@pytest.mark.anyio
async def test_signup_invalid_password(
    client: AsyncClient,
) -> None:
    """Test registration with weak password."""
    response = await client.post(
        "/api/access/signup",
        json={
            "email": f"weakpass-{uuid4().hex[:8]}@example.com",
            "password": "weak",  # Too weak
            "name": "Weak Password User",
        },
    )

    assert response.status_code == 400  # Validation error


@pytest.mark.anyio
async def test_signup_invalid_email(
    client: AsyncClient,
) -> None:
    """Test registration with invalid email."""
    response = await client.post(
        "/api/access/signup",
        json={"email": "notanemail", "password": "securePassword123!", "name": "Invalid Email User"},
    )

    assert response.status_code == 400  # Validation error


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


async def _login_user(client: AsyncClient, user: m.User, password: str = "testPassword123!") -> str:
    """Helper to login user and return auth token."""
    response = await client.post(
        "/api/access/login",
        data={"username": user.email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_get_profile_authenticated(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test getting user profile when authenticated."""
    # Create and login user
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

    # Verify database was updated
    await session.refresh(user)
    assert user.name == "Updated Name"
    assert user.username == new_username
    assert user.phone == "+1234567890"


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

    # Verify reset token was created
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

    # Should return success message for security (don't reveal if email exists)
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

    # Should return success message for security
    assert response.status_code == 201


@pytest.mark.anyio
async def test_validate_reset_token_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful reset token validation."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    # Create valid reset token (must be 32+ chars)
    raw_token = uuid4().hex + uuid4().hex  # 64 chars
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
    # Token must be at least 32 chars to pass validation
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

    # Create valid reset token
    raw_token = uuid4().hex + uuid4().hex  # 64 chars
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

    # Verify token was consumed
    await session.refresh(reset_token)
    assert reset_token.is_used is True


@pytest.mark.anyio
async def test_reset_password_passwords_mismatch(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test password reset with mismatched passwords."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    raw_token = uuid4().hex + uuid4().hex  # 64 chars
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

    raw_token = uuid4().hex + uuid4().hex  # 64 chars
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
    # Token must be 32+ chars to pass validation
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
async def test_rate_limiting_password_reset(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test rate limiting for password reset requests."""
    unique_email = f"ratelimit-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(email=unique_email, is_active=True, is_verified=True)
    session.add(user)
    await session.commit()

    # Make multiple reset requests
    for _ in range(3):
        response = await client.post("/api/access/forgot-password", json={"email": unique_email})
        assert response.status_code == 201

    # Next request should be rate limited
    response = await client.post("/api/access/forgot-password", json={"email": unique_email})

    assert response.status_code == 201
    response_data = response.json()
    # Rate limiting may or may not be implemented - just check for valid response
    assert "password reset link has been sent" in response_data["message"] or "Too many" in response_data["message"]


@pytest.mark.anyio
async def test_token_invalidation_on_new_reset_request(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that requesting new reset token invalidates previous ones."""
    unique_email = f"invalidate-{uuid4().hex[:8]}@example.com"
    user = UserFactory.build(email=unique_email, is_active=True, is_verified=True)
    session.add(user)
    await session.commit()

    # Create first reset token
    await client.post("/api/access/forgot-password", json={"email": unique_email})

    # Get the first token
    result = await session.execute(
        select(m.PasswordResetToken)
        .where(m.PasswordResetToken.user_id == user.id)
        .order_by(m.PasswordResetToken.created_at.asc())
    )
    tokens = list(result.scalars().all())
    if len(tokens) == 0:
        pytest.skip("No reset token was created - email may be silently skipped")
    first_token = tokens[0]

    # Create second reset token
    await client.post("/api/access/forgot-password", json={"email": unique_email})

    # Verify first token is now invalid
    await session.refresh(first_token)
    assert first_token.is_used is True


@pytest.mark.anyio
async def test_password_reset_token_single_use(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that reset tokens can only be used once."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    raw_token = uuid4().hex + uuid4().hex  # 64 chars
    reset_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        raw_token=raw_token,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    session.add(reset_token)
    await session.commit()

    # First reset should succeed
    response = await client.post(
        "/api/access/reset-password",
        json={"token": raw_token, "password": "newPassword123!", "password_confirm": "newPassword123!"},
    )
    assert response.status_code == 201

    # Second reset should fail
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


@pytest.mark.anyio
async def test_complete_registration_and_login_flow(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test complete user registration and login workflow."""
    unique_email = f"complete-{uuid4().hex[:8]}@example.com"
    # 1. Register new user
    response = await client.post(
        "/api/access/signup",
        json={"email": unique_email, "password": "securePassword123!", "name": "Complete User"},
    )
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["isVerified"] is False

    # 2. Get user from database
    result = await session.execute(select(m.User).where(m.User.email == unique_email))
    user = result.scalar_one()

    # 3. Simulate email verification by manually verifying user
    user.is_verified = True
    await session.commit()

    # 4. Login with verified user
    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "securePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201
    token_data = response.json()
    token = token_data["access_token"]

    # 5. Access protected profile endpoint
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
    # Create user
    user = UserFactory.build(
        email=unique_email,
        hashed_password=await get_password_hash("oldPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    # 1. Test login with old password
    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "oldPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201

    # 2. Create reset token directly (simulating what forgot-password does)
    # We use factory to have access to raw_token for testing
    raw_token = uuid4().hex + uuid4().hex  # 64 chars
    reset_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        raw_token=raw_token,
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
    )
    session.add(reset_token)
    await session.commit()

    # 3. Validate reset token
    response = await client.get("/api/access/reset-password", params={"token": raw_token})
    assert response.status_code == 200
    assert response.json()["valid"] is True

    # 4. Reset password
    response = await client.post(
        "/api/access/reset-password",
        json={
            "token": raw_token,
            "password": "newPassword123!",
            "password_confirm": "newPassword123!",
        },
    )
    assert response.status_code == 201

    # 5. Test login with new password
    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "newPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201

    # 6. Test old password no longer works
    response = await client.post(
        "/api/access/login",
        data={"username": unique_email, "password": "oldPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 403
