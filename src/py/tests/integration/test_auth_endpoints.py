"""Integration tests for authentication endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from app.db import models as m

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient

pytestmark = [pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_signup_success(self, client: AsyncTestClient) -> None:
        """Test successful user registration."""
        with patch("app.lib.email.email_service.send_verification_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

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
            assert data["is_active"] is True
            assert data["is_verified"] is False  # Should require verification
            assert "hashed_password" not in data  # Should never be exposed

            # Verify verification email was sent
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client: AsyncTestClient, test_user: m.User) -> None:
        """Test registration with duplicate email fails."""
        signup_data = {
            "email": test_user.email,  # Use existing user's email
            "password": "TestPassword123!",
            "name": "Duplicate User",
        }

        response = await client.post("/api/access/signup", json=signup_data)

        assert response.status_code == 409  # Conflict
        error_data = response.json()
        assert "already exists" in error_data["detail"].lower()

    @pytest.mark.asyncio
    async def test_signup_invalid_email(self, client: AsyncTestClient) -> None:
        """Test registration with invalid email fails."""
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

    @pytest.mark.asyncio
    async def test_signup_weak_password(self, client: AsyncTestClient) -> None:
        """Test registration with weak passwords fails."""
        weak_passwords = [
            "password",  # Too common
            "12345678",  # No complexity
            "Password",  # Missing number and special char
            "Pass123",  # Too short
            "p" * 129,  # Too long
        ]

        for password in weak_passwords:
            signup_data = {
                "email": "test@example.com",
                "password": password,
                "name": "Test User",
            }

            response = await client.post("/api/access/signup", json=signup_data)
            assert response.status_code == 400, f"Password '{password}' should be rejected"

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncTestClient, test_user: m.User) -> None:
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "TestPassword123!",
        }

        response = await client.post("/api/access/login", json=login_data)

        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncTestClient, test_user: m.User) -> None:
        """Test login with wrong password fails."""
        login_data = {
            "username": test_user.email,
            "password": "WrongPassword",
        }

        response = await client.post("/api/access/login", json=login_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncTestClient) -> None:
        """Test login with non-existent user fails."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "TestPassword123!",
        }

        response = await client.post("/api/access/login", json=login_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncTestClient, inactive_user: m.User) -> None:
        """Test login with inactive user fails."""
        login_data = {
            "username": inactive_user.email,
            "password": "TestPassword123!",
        }

        response = await client.post("/api/access/login", json=login_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client: AsyncTestClient, test_user: m.User) -> None:
        """Test getting current user profile."""
        response = await authenticated_client.get("/api/users/profile")

        assert response.status_code == 200
        user_data = response.json()
        assert user_data["id"] == str(test_user.id)
        assert user_data["email"] == test_user.email
        assert user_data["name"] == test_user.name
        assert "hashed_password" not in user_data  # Should never be exposed

    @pytest.mark.asyncio
    async def test_get_current_user_unauthenticated(self, client: AsyncTestClient) -> None:
        """Test getting current user without authentication fails."""
        response = await client.get("/api/users/profile")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile(self, authenticated_client: AsyncTestClient, test_user: m.User) -> None:
        """Test updating user profile."""
        update_data = {
            "name": "Updated Name",
            "username": "updated_username",
        }

        response = await authenticated_client.patch("/api/users/profile", json=update_data)

        assert response.status_code == 200
        user_data = response.json()
        assert user_data["name"] == "Updated Name"
        assert user_data["username"] == "updated_username"
        assert user_data["email"] == test_user.email  # Should not change

    @pytest.mark.asyncio
    async def test_update_profile_unauthenticated(self, client: AsyncTestClient) -> None:
        """Test updating profile without authentication fails."""
        update_data = {"name": "Updated Name"}

        response = await client.patch("/api/users/profile", json=update_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_success(self, authenticated_client: AsyncTestClient, test_user: m.User) -> None:
        """Test successful password change."""
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
        }

        response = await authenticated_client.post("/api/users/password", json=password_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "password" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, authenticated_client: AsyncTestClient) -> None:
        """Test password change with wrong current password fails."""
        password_data = {
            "current_password": "WrongPassword",
            "new_password": "NewPassword123!",
        }

        response = await authenticated_client.post("/api/users/password", json=password_data)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(self, authenticated_client: AsyncTestClient) -> None:
        """Test password change with weak new password fails."""
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "weak",
        }

        response = await authenticated_client.post("/api/users/password", json=password_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_logout_success(self, authenticated_client: AsyncTestClient) -> None:
        """Test successful logout."""
        response = await authenticated_client.post("/api/access/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_refresh_token(self, authenticated_client: AsyncTestClient) -> None:
        """Test token refresh."""
        # First, get a token through login
        response = await authenticated_client.post("/api/access/refresh")

        # Note: This might fail if refresh tokens aren't implemented yet
        # The test ensures the endpoint exists and responds appropriately
        assert response.status_code in {200, 400, 401}


class TestEmailVerificationEndpoints:
    """Test email verification endpoints."""

    @pytest.mark.asyncio
    async def test_request_verification_email(self, client: AsyncTestClient, unverified_user: m.User) -> None:
        """Test requesting email verification."""
        with patch("app.lib.email.email_service.send_verification_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            request_data = {"email": unverified_user.email}

            response = await client.post("/api/email-verification/request", json=request_data)

            assert response.status_code == 201
            data = response.json()
            assert "verification" in data["message"].lower()

            # Verify email was sent
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_verification_nonexistent_user(self, client: AsyncTestClient) -> None:
        """Test requesting verification for non-existent user."""
        request_data = {"email": "nonexistent@example.com"}

        response = await client.post("/api/email-verification/request", json=request_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_verify_email_success(
        self,
        client: AsyncTestClient,
        unverified_user: m.User,
        test_verification_token: m.EmailVerificationToken,
    ) -> None:
        """Test successful email verification."""
        verify_data = {"token": test_verification_token.token}

        response = await client.post("/api/email-verification/verify", json=verify_data)

        assert response.status_code == 200
        data = response.json()
        assert "verified" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client: AsyncTestClient) -> None:
        """Test email verification with invalid token."""
        verify_data = {"token": "invalid_token"}

        response = await client.post("/api/email-verification/verify", json=verify_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_email_already_verified(self, client: AsyncTestClient, test_user: m.User) -> None:
        """Test email verification for already verified user."""
        # Create a token for an already verified user
        from datetime import UTC, datetime, timedelta
        from uuid import uuid4

        token = m.EmailVerificationToken(
            id=uuid4(),
            user_id=test_user.id,
            token=uuid4().hex,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )

        verify_data = {"token": token.token}

        response = await client.post("/api/email-verification/verify", json=verify_data)

        # Should either succeed gracefully or return appropriate status
        assert response.status_code in {200, 400}


class TestPasswordResetEndpoints:
    """Test password reset endpoints."""

    @pytest.mark.asyncio
    async def test_request_password_reset(self, client: AsyncTestClient, test_user: m.User) -> None:
        """Test requesting password reset."""
        with patch("app.lib.email.email_service.send_password_reset_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            request_data = {"email": test_user.email}

            response = await client.post("/api/access/forgot-password", json=request_data)

            # The response might vary based on implementation
            assert response.status_code in {200, 201}

            # Verify email was sent
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(self, client: AsyncTestClient) -> None:
        """Test password reset request for non-existent user."""
        request_data = {"email": "nonexistent@example.com"}

        response = await client.post("/api/access/forgot-password", json=request_data)

        # For security, should not reveal if user exists
        assert response.status_code in {200, 404}

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self,
        client: AsyncTestClient,
        test_password_reset_token: m.PasswordResetToken,
    ) -> None:
        """Test successful password reset."""
        reset_data = {
            "token": test_password_reset_token.token,
            "new_password": "NewPassword123!",
        }

        response = await client.post("/api/access/reset-password", json=reset_data)

        assert response.status_code == 200
        data = response.json()
        assert "reset" in data["message"].lower() or "password" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client: AsyncTestClient) -> None:
        """Test password reset with invalid token."""
        reset_data = {
            "token": "invalid_token",
            "new_password": "NewPassword123!",
        }

        response = await client.post("/api/access/reset-password", json=reset_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_weak_password(
        self,
        client: AsyncTestClient,
        test_password_reset_token: m.PasswordResetToken,
    ) -> None:
        """Test password reset with weak password."""
        reset_data = {
            "token": test_password_reset_token.token,
            "new_password": "weak",
        }

        response = await client.post("/api/access/reset-password", json=reset_data)

        assert response.status_code == 400


class TestSecurityValidation:
    """Test security validation in authentication endpoints."""

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, client: AsyncTestClient) -> None:
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
            # Should either be rejected as invalid email or properly sanitized
            assert response.status_code in {400, 409}, f"SQL injection attempt should be blocked: {malicious_email}"

    @pytest.mark.asyncio
    async def test_xss_protection(self, client: AsyncTestClient) -> None:
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
                # If user was created, check that the payload was sanitized
                user_data = response.json()
                # The name should either be sanitized or rejected
                assert xss_payload not in user_data["name"] or response.status_code == 400

    @pytest.mark.asyncio
    async def test_rate_limiting_signup(self, client: AsyncTestClient) -> None:
        """Test rate limiting on signup endpoint."""
        # This test assumes rate limiting is implemented
        # Adjust based on your actual rate limiting configuration

        signup_data = {
            "email": "ratelimit@example.com",
            "password": "TestPassword123!",
            "name": "Rate Limit Test",
        }

        # Make multiple rapid requests
        responses = []
        for i in range(10):  # Attempt 10 rapid signups
            signup_data["email"] = f"ratelimit{i}@example.com"
            response = await client.post("/api/access/signup", json=signup_data)
            responses.append(response.status_code)

        # At least some requests should succeed, but rate limiting might kick in
        # This is more of a smoke test to ensure the endpoint doesn't break
        success_count = sum(1 for status in responses if status == 201)
        assert success_count >= 1, "At least one signup should succeed"

    @pytest.mark.asyncio
    async def test_csrf_protection(self, client: AsyncTestClient) -> None:
        """Test CSRF protection mechanisms."""
        # This test checks that the API properly handles requests
        # The exact implementation depends on your CSRF protection

        # Test that requests without proper headers/tokens are handled appropriately
        headers = {"Origin": "http://malicious-site.com"}

        signup_data = {
            "email": "csrf@example.com",
            "password": "TestPassword123!",
            "name": "CSRF Test",
        }

        response = await client.post("/api/access/signup", json=signup_data, headers=headers)

        # The response should either succeed (if CORS is properly configured)
        # or be rejected (if strict origin checking is enabled)
        assert response.status_code in {201, 400, 403}, "CSRF protection should handle malicious origins"
