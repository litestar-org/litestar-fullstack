"""Integration tests for email service with real email verification and password reset flows."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar_email import EmailMultiAlternatives, InMemoryBackend

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def clear_email_outbox() -> None:
    """Clear email outbox before each test."""
    InMemoryBackend.clear()


async def test_user_registration_triggers_verification_email(
    client: AsyncTestClient,
) -> None:
    """Test that registering a user triggers the email service."""
    unique_email = f"newuser_{uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/access/signup",
        json={
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "New User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email

    # Check that verification email was sent
    assert len(InMemoryBackend.outbox) == 1
    message = InMemoryBackend.outbox[0]
    assert unique_email in message.to
    assert "verify" in message.subject.lower()


async def test_resend_verification_triggers_email_service(
    client: AsyncTestClient,
) -> None:
    """Test resending verification email triggers the email service."""
    unique_email = f"resendtest_{uuid4().hex[:8]}@example.com"
    # First register a user
    response = await client.post(
        "/api/access/signup",
        json={
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "Resend Test",
        },
    )
    assert response.status_code == 201

    # Clear the outbox after signup
    InMemoryBackend.clear()

    # Request resend
    response = await client.post("/api/email-verification/request", json={"email": unique_email})
    assert response.status_code == 201

    # Check that email was sent
    assert len(InMemoryBackend.outbox) == 1
    message = InMemoryBackend.outbox[0]
    assert unique_email in message.to


async def test_password_reset_request_triggers_email_service(
    client: AsyncTestClient,
) -> None:
    """Test that requesting password reset triggers the email service."""
    unique_email = f"resettest_{uuid4().hex[:8]}@example.com"
    # First create a user
    response = await client.post(
        "/api/access/signup",
        json={
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "Reset Test",
        },
    )
    assert response.status_code == 201

    # Clear the outbox after signup
    InMemoryBackend.clear()

    # Request password reset
    response = await client.post("/api/access/forgot-password", json={"email": unique_email})

    assert response.status_code == 201
    data = response.json()
    assert "reset" in data["message"].lower() or "password" in data["message"].lower()

    # Check that reset email was sent
    assert len(InMemoryBackend.outbox) == 1
    message = InMemoryBackend.outbox[0]
    assert unique_email in message.to
    assert "reset" in message.subject.lower()


async def test_registration_sends_verification_email_with_correct_content(
    client: AsyncTestClient,
) -> None:
    """Test that registration sends a proper verification email."""
    unique_email = f"content_test_{uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/access/signup",
        json={
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "Content Test User",
        },
    )

    assert response.status_code == 201

    # Check email content
    assert len(InMemoryBackend.outbox) == 1
    message = InMemoryBackend.outbox[0]
    assert unique_email in message.to

    # HTML body should contain verification link
    assert isinstance(message, EmailMultiAlternatives)
    assert message.html_body is not None
    assert "verify" in message.html_body.lower()


async def test_multiple_signups_send_multiple_emails(
    client: AsyncTestClient,
) -> None:
    """Test that multiple signups each send their own verification email."""
    unique_suffix = uuid4().hex[:8]
    users = [
        {"email": f"user1_{unique_suffix}@example.com", "name": "User One"},
        {"email": f"user2_{unique_suffix}@example.com", "name": "User Two"},
        {"email": f"user3_{unique_suffix}@example.com", "name": "User Three"},
    ]

    for user in users:
        response = await client.post(
            "/api/access/signup",
            json={
                "email": user["email"],
                "password": "TestPassword123!",
                "name": user["name"],
            },
        )
        assert response.status_code == 201

    # Check that all emails were sent
    assert len(InMemoryBackend.outbox) == 3

    sent_to = [msg.to[0] for msg in InMemoryBackend.outbox]
    for user in users:
        assert user["email"] in sent_to
