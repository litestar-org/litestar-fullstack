"""Integration tests for authentication endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from litestar.testing import AsyncTestClient
from sqlalchemy import select

from app.db import models as m
from app.lib.crypt import get_password_hash
from tests.factories import PasswordResetTokenFactory, UserFactory

if TYPE_CHECKING:
    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]


class TestAccountLogin:
    """Test authentication login endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test successful user login."""
        # Create verified user with known password
        user = UserFactory.build(
            email="login@example.com",
            hashed_password=await get_password_hash("securePassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/login",
                data={"username": "login@example.com", "password": "securePassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            assert response.status_code == 200
            response_data = response.json()
            assert "access_token" in response_data
            assert response_data["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test login with invalid credentials."""
        # Create user
        user = UserFactory.build(
            email="login@example.com",
            hashed_password=await get_password_hash("securePassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/login",
                data={"username": "login@example.com", "password": "wrongPassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            assert response.status_code == 401
            assert "Invalid credentials" in response.text

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test login with inactive user."""
        user = UserFactory.build(
            email="inactive@example.com",
            hashed_password=await get_password_hash("securePassword123!"),
            is_active=False,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/login",
                data={"username": "inactive@example.com", "password": "securePassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unverified_user(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test login with unverified user."""
        user = UserFactory.build(
            email="unverified@example.com",
            hashed_password=await get_password_hash("securePassword123!"),
            is_active=True,
            is_verified=False,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/login",
                data={"username": "unverified@example.com", "password": "securePassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
        self,
        app: Litestar,
    ) -> None:
        """Test login with non-existent user."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/login",
                data={"username": "nonexistent@example.com", "password": "anyPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(
        self,
        app: Litestar,
    ) -> None:
        """Test login with invalid email format."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/login",
                data={"username": "notanemail", "password": "anyPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            assert response.status_code == 422  # Validation error


class TestAccountLogout:
    """Test authentication logout endpoints."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        app: Litestar,
    ) -> None:
        """Test successful logout."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post("/api/access/logout")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["message"] == "OK"


class TestAccountRegistration:
    """Test user registration endpoints."""

    @pytest.mark.asyncio
    async def test_signup_success(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test successful user registration."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/signup",
                json={
                    "email": "newuser@example.com",
                    "password": "securePassword123!",
                    "name": "New User",
                    "username": "newuser",
                },
            )

            assert response.status_code == 201
            response_data = response.json()
            assert response_data["email"] == "newuser@example.com"
            assert response_data["name"] == "New User"
            assert response_data["username"] == "newuser"
            assert response_data["isVerified"] is False  # Requires email verification
            assert response_data["isActive"] is True

        # Verify user was created in database
        result = await session.execute(select(m.User).where(m.User.email == "newuser@example.com"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.is_verified is False

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test registration with duplicate email."""
        # Create existing user
        existing_user = UserFactory.build(email="existing@example.com")
        session.add(existing_user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/signup",
                json={"email": "existing@example.com", "password": "securePassword123!", "name": "Duplicate User"},
            )

            assert response.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_signup_invalid_password(
        self,
        app: Litestar,
    ) -> None:
        """Test registration with weak password."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/signup",
                json={
                    "email": "weakpass@example.com",
                    "password": "weak",  # Too weak
                    "name": "Weak Password User",
                },
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_signup_invalid_email(
        self,
        app: Litestar,
    ) -> None:
        """Test registration with invalid email."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/signup",
                json={"email": "notanemail", "password": "securePassword123!", "name": "Invalid Email User"},
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_signup_minimal_data(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test registration with minimal required data."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/signup", json={"email": "minimal@example.com", "password": "securePassword123!"}
            )

            assert response.status_code == 201
            response_data = response.json()
            assert response_data["email"] == "minimal@example.com"
            assert response_data["name"] is None
            assert response_data["username"] is None


class TestUserProfileManagement:
    """Test user profile management endpoints."""

    async def _login_user(self, client: AsyncTestClient, user: m.User) -> str:
        """Helper to login user and return auth token."""
        response = await client.post(
            "/api/access/login",
            data={"username": user.email, "password": "testPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_get_profile_authenticated(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test getting user profile when authenticated."""
        # Create and login user
        user = UserFactory.build(
            email="profile@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
            name="Profile User",
            username="profileuser",
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            response = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["email"] == "profile@example.com"
            assert response_data["name"] == "Profile User"
            assert response_data["username"] == "profileuser"

    @pytest.mark.asyncio
    async def test_get_profile_unauthenticated(
        self,
        app: Litestar,
    ) -> None:
        """Test getting user profile without authentication."""
        async with AsyncTestClient(app=app) as client:
            response = await client.get("/api/me")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_success(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test successful profile update."""
        user = UserFactory.build(
            email="update@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
            name="Original Name",
            username="originaluser",
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            response = await client.patch(
                "/api/me",
                json={"name": "Updated Name", "username": "updateduser", "phone": "+1234567890"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["name"] == "Updated Name"
            assert response_data["username"] == "updateduser"
            assert response_data["phone"] == "+1234567890"

        # Verify database was updated
        await session.refresh(user)
        assert user.name == "Updated Name"
        assert user.username == "updateduser"
        assert user.phone == "+1234567890"

    @pytest.mark.asyncio
    async def test_update_password_success(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test successful password update."""
        user = UserFactory.build(
            email="password@example.com",
            hashed_password=await get_password_hash("oldPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            response = await client.patch(
                "/api/me/password",
                json={"currentPassword": "oldPassword123!", "newPassword": "newPassword123!"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["message"] == "Your password was successfully modified."

    @pytest.mark.asyncio
    async def test_update_password_wrong_current(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test password update with wrong current password."""
        user = UserFactory.build(
            email="password@example.com",
            hashed_password=await get_password_hash("correctPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            response = await client.patch(
                "/api/me/password",
                json={"currentPassword": "wrongPassword123!", "newPassword": "newPassword123!"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 400


class TestPasswordReset:
    """Test password reset flow endpoints."""

    @pytest.mark.asyncio
    async def test_forgot_password_success(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test successful forgot password request."""
        user = UserFactory.build(email="reset@example.com", is_active=True, is_verified=True)
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post("/api/access/forgot-password", json={"email": "reset@example.com"})

            assert response.status_code == 200
            response_data = response.json()
            assert "password reset link has been sent" in response_data["message"]
            assert response_data["expiresInMinutes"] == 60

        # Verify reset token was created
        result = await session.execute(select(m.PasswordResetToken).where(m.PasswordResetToken.user_id == user.id))
        token = result.scalar_one_or_none()
        assert token is not None
        assert token.is_valid is True

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_user(
        self,
        app: Litestar,
    ) -> None:
        """Test forgot password for non-existent user."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post("/api/access/forgot-password", json={"email": "nonexistent@example.com"})

            # Should return success message for security (don't reveal if email exists)
            assert response.status_code == 200
            response_data = response.json()
            assert "password reset link has been sent" in response_data["message"]

    @pytest.mark.asyncio
    async def test_forgot_password_inactive_user(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test forgot password for inactive user."""
        user = UserFactory.build(email="inactive@example.com", is_active=False, is_verified=True)
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post("/api/access/forgot-password", json={"email": "inactive@example.com"})

            # Should return success message for security
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_validate_reset_token_success(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test successful reset token validation."""
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        # Create valid reset token
        reset_token = PasswordResetTokenFactory.build(
            user_id=user.id,
            token="valid_token_123",
            expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        )
        session.add(reset_token)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.get("/api/access/reset-password", params={"token": "valid_token_123"})

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["valid"] is True
            assert response_data["userId"] == str(user.id)

    @pytest.mark.asyncio
    async def test_validate_reset_token_invalid(
        self,
        app: Litestar,
    ) -> None:
        """Test validation of invalid reset token."""
        async with AsyncTestClient(app=app) as client:
            response = await client.get("/api/access/reset-password", params={"token": "invalid_token"})

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["valid"] is False

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test successful password reset."""
        user = UserFactory.build(email="reset@example.com", hashed_password=await get_password_hash("oldPassword123!"))
        session.add(user)
        await session.commit()

        # Create valid reset token
        reset_token = PasswordResetTokenFactory.build(
            user_id=user.id,
            token="reset_token_123",
            expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        )
        session.add(reset_token)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/reset-password",
                json={"token": "reset_token_123", "password": "newPassword123!", "passwordConfirm": "newPassword123!"},
            )

            assert response.status_code == 200
            response_data = response.json()
            assert "successfully reset" in response_data["message"]
            assert response_data["userId"] == str(user.id)

        # Verify token was consumed
        await session.refresh(reset_token)
        assert reset_token.is_used is True

    @pytest.mark.asyncio
    async def test_reset_password_passwords_mismatch(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test password reset with mismatched passwords."""
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        reset_token = PasswordResetTokenFactory.build(
            user_id=user.id,
            token="reset_token_123",
            expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        )
        session.add(reset_token)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/reset-password",
                json={
                    "token": "reset_token_123",
                    "password": "newPassword123!",
                    "passwordConfirm": "differentPassword123!",
                },
            )

            assert response.status_code == 400
            assert "do not match" in response.text

    @pytest.mark.asyncio
    async def test_reset_password_weak_password(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test password reset with weak password."""
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        reset_token = PasswordResetTokenFactory.build(
            user_id=user.id,
            token="reset_token_123",
            expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        )
        session.add(reset_token)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/reset-password",
                json={"token": "reset_token_123", "password": "weak", "passwordConfirm": "weak"},
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(
        self,
        app: Litestar,
    ) -> None:
        """Test password reset with invalid token."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/reset-password",
                json={"token": "invalid_token", "password": "newPassword123!", "passwordConfirm": "newPassword123!"},
            )

            assert response.status_code == 400
            assert "Invalid reset token" in response.text


class TestAuthenticationSecurity:
    """Test authentication security features."""

    @pytest.mark.asyncio
    async def test_rate_limiting_password_reset(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test rate limiting for password reset requests."""
        user = UserFactory.build(email="ratelimit@example.com", is_active=True, is_verified=True)
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Make multiple reset requests
            for _ in range(3):
                response = await client.post("/api/access/forgot-password", json={"email": "ratelimit@example.com"})
                assert response.status_code == 200

            # Next request should be rate limited
            response = await client.post("/api/access/forgot-password", json={"email": "ratelimit@example.com"})

            assert response.status_code == 200
            response_data = response.json()
            assert "Too many" in response_data["message"]

    @pytest.mark.asyncio
    async def test_token_invalidation_on_new_reset_request(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test that requesting new reset token invalidates previous ones."""
        user = UserFactory.build(email="invalidate@example.com", is_active=True, is_verified=True)
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Create first reset token
            await client.post("/api/access/forgot-password", json={"email": "invalidate@example.com"})

            # Get the first token
            result = await session.execute(select(m.PasswordResetToken).where(m.PasswordResetToken.user_id == user.id))
            first_token = result.scalar_one()

            # Create second reset token
            await client.post("/api/access/forgot-password", json={"email": "invalidate@example.com"})

            # Verify first token is now invalid
            await session.refresh(first_token)
            assert first_token.is_used is True

    @pytest.mark.asyncio
    async def test_password_reset_token_single_use(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test that reset tokens can only be used once."""
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        reset_token = PasswordResetTokenFactory.build(
            user_id=user.id,
            token="single_use_token",
            expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        )
        session.add(reset_token)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # First reset should succeed
            response = await client.post(
                "/api/access/reset-password",
                json={"token": "single_use_token", "password": "newPassword123!", "passwordConfirm": "newPassword123!"},
            )
            assert response.status_code == 200

            # Second reset should fail
            response = await client.post(
                "/api/access/reset-password",
                json={
                    "token": "single_use_token",
                    "password": "anotherPassword123!",
                    "passwordConfirm": "anotherPassword123!",
                },
            )
            assert response.status_code == 400
            assert "already been used" in response.text


class TestAuthenticationIntegration:
    """Integration tests for complete authentication workflows."""

    @pytest.mark.asyncio
    async def test_complete_registration_and_login_flow(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test complete user registration and login workflow."""
        async with AsyncTestClient(app=app) as client:
            # 1. Register new user
            response = await client.post(
                "/api/access/signup",
                json={"email": "complete@example.com", "password": "securePassword123!", "name": "Complete User"},
            )
            assert response.status_code == 201
            user_data = response.json()
            assert user_data["isVerified"] is False

            # 2. Get user from database
            result = await session.execute(select(m.User).where(m.User.email == "complete@example.com"))
            user = result.scalar_one()

            # 3. Simulate email verification by manually verifying user
            user.is_verified = True
            await session.commit()

            # 4. Login with verified user
            response = await client.post(
                "/api/access/login",
                data={"username": "complete@example.com", "password": "securePassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 200
            token_data = response.json()
            token = token_data["access_token"]

            # 5. Access protected profile endpoint
            response = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            profile_data = response.json()
            assert profile_data["email"] == "complete@example.com"
            assert profile_data["name"] == "Complete User"

    @pytest.mark.asyncio
    async def test_complete_password_reset_flow(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test complete password reset workflow."""
        # Create user
        user = UserFactory.build(
            email="resetflow@example.com",
            hashed_password=await get_password_hash("oldPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # 1. Test login with old password
            response = await client.post(
                "/api/access/login",
                data={"username": "resetflow@example.com", "password": "oldPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 200

            # 2. Request password reset
            response = await client.post("/api/access/forgot-password", json={"email": "resetflow@example.com"})
            assert response.status_code == 200

            # 3. Get reset token from database
            result = await session.execute(select(m.PasswordResetToken).where(m.PasswordResetToken.user_id == user.id))
            reset_token = result.scalar_one()

            # 4. Validate reset token
            response = await client.get("/api/access/reset-password", params={"token": reset_token.raw_token})
            assert response.status_code == 200
            assert response.json()["valid"] is True

            # 5. Reset password
            response = await client.post(
                "/api/access/reset-password",
                json={
                    "token": reset_token.raw_token,
                    "password": "newPassword123!",
                    "passwordConfirm": "newPassword123!",
                },
            )
            assert response.status_code == 200

            # 6. Test login with new password
            response = await client.post(
                "/api/access/login",
                data={"username": "resetflow@example.com", "password": "newPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 200

            # 7. Test old password no longer works
            response = await client.post(
                "/api/access/login",
                data={"username": "resetflow@example.com", "password": "oldPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 401
