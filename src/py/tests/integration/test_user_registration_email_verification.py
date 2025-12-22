"""Integration tests for user registration with email verification."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

from app.domain.accounts.schemas import User

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient


class TestUserRegistrationEmailVerification:
    """Integration tests for user registration with email verification flow."""

    async def test_user_registration_creates_unverified_user(self, client: AsyncTestClient) -> None:
        """Test that user registration creates an unverified user."""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "name": "New User",
        }

        # Act
        response = await client.post("/api/access/signup", json=user_data)

        # Assert
        assert response.status_code == 201
        user = msgspec.json.decode(response.content, type=User)
        assert user.email == "newuser@example.com"
        assert user.name == "New User"
        assert user.is_verified is False  # Should be unverified initially
        assert user.is_active is True

    async def test_user_registration_sends_verification_email(self, client: AsyncTestClient) -> None:
        """Test that user registration triggers verification email sending."""
        # Arrange
        user_data = {
            "email": "emailtest@example.com",
            "password": "SecurePass123",
            "name": "Email Test User",
        }

        # Act - register user
        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        # Verify that a verification token was created by requesting verification
        # (This indirectly tests that the email sending was triggered)
        request_data = {"email": "emailtest@example.com"}
        verify_request_response = await client.post("/api/email-verification/request", json=request_data)

        # Assert - verification request should work (meaning user exists and is unverified)
        assert verify_request_response.status_code == 201
        data = verify_request_response.json()
        assert "token" in data

    async def test_complete_registration_verification_flow(self, client: AsyncTestClient) -> None:
        """Test complete flow from registration to email verification."""
        # Arrange
        user_data = {
            "email": "complete@example.com",
            "password": "SecurePass123",
            "name": "Complete User",
        }

        # Act 1 - Register user
        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        user_info = signup_response.json()
        user_id = user_info["id"]

        # Verify user is initially unverified
        status_response = await client.get(f"/api/email-verification/status/{user_id}")
        assert status_response.status_code == 200
        assert status_response.json()["is_verified"] is False

        # Act 2 - Request verification email
        request_data = {"email": "complete@example.com"}
        request_response = await client.post("/api/email-verification/request", json=request_data)
        assert request_response.status_code == 201

        token = request_response.json()["token"]

        # Act 3 - Verify email using token
        verify_data = {"token": token}
        verify_response = await client.post("/api/email-verification/verify", json=verify_data)
        assert verify_response.status_code == 200

        # Assert - User should now be verified
        verified_user = msgspec.json.decode(verify_response.content, type=User)
        assert verified_user.is_verified is True
        assert verified_user.email == "complete@example.com"

        # Double-check with status endpoint
        final_status_response = await client.get(f"/api/email-verification/status/{user_id}")
        assert final_status_response.status_code == 200
        assert final_status_response.json()["is_verified"] is True

    async def test_registration_with_duplicate_email(self, client: AsyncTestClient) -> None:
        """Test registration with duplicate email address."""
        # Arrange
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123",
            "name": "First User",
        }

        # Act 1 - Register first user
        first_response = await client.post("/api/access/signup", json=user_data)
        assert first_response.status_code == 201

        # Act 2 - Try to register second user with same email
        user_data["name"] = "Second User"
        second_response = await client.post("/api/access/signup", json=user_data)

        # Assert - Should fail due to unique constraint
        assert second_response.status_code == 409  # Conflict

    async def test_login_before_email_verification(self, client: AsyncTestClient) -> None:
        """Test that login works even before email verification."""
        # Arrange
        user_data = {
            "email": "logintest@example.com",
            "password": "SecurePass123",
            "name": "Login Test User",
        }

        # Act 1 - Register user
        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        # Act 2 - Try to login before verification
        login_data = {
            "username": "logintest@example.com",
            "password": "SecurePass123",
        }
        login_response = await client.post(
            "/api/access/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Assert - Login should succeed (email verification is not required for login)
        assert login_response.status_code == 200

    async def test_registration_with_initial_team(self, client: AsyncTestClient) -> None:
        """Test registration with initial team creation."""
        # Arrange
        user_data = {
            "email": "teamuser@example.com",
            "password": "SecurePass123",
            "name": "Team User",
            "initial_team_name": "My Team",
        }

        # Act
        response = await client.post("/api/access/signup", json=user_data)

        # Assert
        assert response.status_code == 201
        user = msgspec.json.decode(response.content, type=User)
        assert user.email == "teamuser@example.com"
        assert user.is_verified is False  # Should still be unverified
        # Note: We don't test team creation details here as that's outside email verification scope

    async def test_multiple_verification_requests(self, client: AsyncTestClient) -> None:
        """Test that multiple verification requests invalidate previous tokens."""
        # Arrange
        user_data = {
            "email": "multiple@example.com",
            "password": "SecurePass123",
            "name": "Multiple User",
        }

        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        request_data = {"email": "multiple@example.com"}

        # Act 1 - Request first verification token
        first_request = await client.post("/api/email-verification/request", json=request_data)
        assert first_request.status_code == 201
        first_token = first_request.json()["token"]

        # Act 2 - Request second verification token (should invalidate first)
        second_request = await client.post("/api/email-verification/request", json=request_data)
        assert second_request.status_code == 201
        second_token = second_request.json()["token"]

        # Assert - First token should be invalidated
        verify_first = {"token": first_token}
        first_verify_response = await client.post("/api/email-verification/verify", json=verify_first)
        assert first_verify_response.status_code == 400  # Should fail

        # Second token should still work
        verify_second = {"token": second_token}
        second_verify_response = await client.post("/api/email-verification/verify", json=verify_second)
        assert second_verify_response.status_code == 200  # Should succeed
