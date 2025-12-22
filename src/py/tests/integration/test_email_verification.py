"""Integration tests for email verification API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import msgspec

from app.domain.accounts.schemas import User

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient


class TestEmailVerificationIntegration:
    """Integration tests for email verification endpoints."""

    async def test_request_verification_success(self, client: AsyncTestClient) -> None:
        """Test successful verification email request."""
        # Arrange - create a user first via signup
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123",
            "name": "Test User",
        }

        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        # Act - request verification email
        request_data = {"email": "test@example.com"}
        response = await client.post("/api/email-verification/request", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Verification email sent"
        assert "token" in data  # Token should be present for testing

    async def test_request_verification_nonexistent_email(self, client: AsyncTestClient) -> None:
        """Test verification request for non-existent email."""
        # Arrange
        request_data = {"email": "nonexistent@example.com"}

        # Act
        response = await client.post("/api/email-verification/request", json=request_data)

        # Assert - should not reveal if email exists
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "If the email exists, a verification link has been sent"

    async def test_request_verification_already_verified(self, client: AsyncTestClient) -> None:
        """Test verification request for already verified email."""
        # Arrange - create and verify a user
        user_data = {
            "email": "verified@example.com",
            "password": "SecurePass123",
            "name": "Verified User",
        }

        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        # Get the verification token from signup and verify
        # First get a verification token
        request_data = {"email": "verified@example.com"}
        request_response = await client.post("/api/email-verification/request", json=request_data)
        assert request_response.status_code == 201

        token = request_response.json()["token"]

        # Verify the email
        verify_data = {"token": token}
        verify_response = await client.post("/api/email-verification/verify", json=verify_data)
        assert verify_response.status_code == 200

        # Act - request verification again
        response = await client.post("/api/email-verification/request", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Email is already verified"

    async def test_verify_email_success(self, client: AsyncTestClient) -> None:
        """Test successful email verification."""
        # Arrange - create user and get verification token
        user_data = {
            "email": "verify@example.com",
            "password": "SecurePass123",
            "name": "Verify User",
        }

        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        # Request verification token
        request_data = {"email": "verify@example.com"}
        request_response = await client.post("/api/email-verification/request", json=request_data)
        assert request_response.status_code == 201

        token = request_response.json()["token"]

        # Act - verify email
        verify_data = {"token": token}
        response = await client.post("/api/email-verification/verify", json=verify_data)

        # Assert
        assert response.status_code == 200
        user = msgspec.json.decode(response.content, type=User)
        assert user.is_verified is True
        assert user.email == "verify@example.com"

    async def test_verify_email_invalid_token(self, client: AsyncTestClient) -> None:
        """Test email verification with invalid token."""
        # Arrange
        verify_data = {"token": "invalid_token_12345"}

        # Act
        response = await client.post("/api/email-verification/verify", json=verify_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid verification token" in data["detail"]

    async def test_verify_email_token_reuse_prevention(self, client: AsyncTestClient) -> None:
        """Test that tokens cannot be reused."""
        # Arrange - create user and get verification token
        user_data = {
            "email": "reuse@example.com",
            "password": "SecurePass123",
            "name": "Reuse User",
        }

        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        # Request verification token
        request_data = {"email": "reuse@example.com"}
        request_response = await client.post("/api/email-verification/request", json=request_data)
        assert request_response.status_code == 201

        token = request_response.json()["token"]

        # Act - verify email first time
        verify_data = {"token": token}
        first_response = await client.post("/api/email-verification/verify", json=verify_data)
        assert first_response.status_code == 200

        # Act - try to verify again with same token
        second_response = await client.post("/api/email-verification/verify", json=verify_data)

        # Assert - should fail
        assert second_response.status_code == 400
        data = second_response.json()
        assert "already been used" in data["detail"]

    async def test_get_verification_status_verified(self, client: AsyncTestClient) -> None:
        """Test getting verification status for verified user."""
        # Arrange - create and verify user
        user_data = {
            "email": "status@example.com",
            "password": "SecurePass123",
            "name": "Status User",
        }

        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        user_info = signup_response.json()
        user_id = user_info["id"]

        # Request and use verification token
        request_data = {"email": "status@example.com"}
        request_response = await client.post("/api/email-verification/request", json=request_data)
        token = request_response.json()["token"]

        verify_data = {"token": token}
        await client.post("/api/email-verification/verify", json=verify_data)

        # Act - check status
        response = await client.get(f"/api/email-verification/status/{user_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True

    async def test_get_verification_status_unverified(self, client: AsyncTestClient) -> None:
        """Test getting verification status for unverified user."""
        # Arrange - create user without verifying
        user_data = {
            "email": "unverified@example.com",
            "password": "SecurePass123",
            "name": "Unverified User",
        }

        signup_response = await client.post("/api/access/signup", json=user_data)
        assert signup_response.status_code == 201

        user_info = signup_response.json()
        user_id = user_info["id"]

        # Act - check status
        response = await client.get(f"/api/email-verification/status/{user_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is False

    async def test_get_verification_status_nonexistent_user(self, client: AsyncTestClient) -> None:
        """Test getting verification status for non-existent user."""
        # Arrange
        fake_user_id = str(uuid4())

        # Act
        response = await client.get(f"/api/email-verification/status/{fake_user_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is False
