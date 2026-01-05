"""Unit tests for AppEmailService functionality."""

from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest
from litestar_email import EmailConfig, EmailService, InMemoryBackend

from app.db import models as m
from app.lib.email import AppEmailService

if TYPE_CHECKING:
    from app.lib.email.service import UserProtocol

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def clear_email_outbox() -> None:
    """Clear email outbox before each test."""
    InMemoryBackend.clear()


@pytest.fixture
def mailer() -> EmailService:
    """Create EmailService instance with in-memory backend."""
    config = EmailConfig(backend="memory")
    return EmailService(config=config)


@pytest.fixture
def app_email_service(mailer: EmailService) -> AppEmailService:
    """Create AppEmailService instance."""
    return AppEmailService(mailer=mailer)


@pytest.fixture
def user() -> m.User:
    """Create test user."""
    return m.User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        is_active=True,
        is_verified=False,
        is_superuser=False,
        login_count=0,
    )


@pytest.fixture
def user_without_name() -> m.User:
    """Create test user without name."""
    return m.User(
        id=uuid4(),
        email="noname@example.com",
        name=None,
        is_active=True,
        is_verified=False,
        is_superuser=False,
        login_count=0,
    )


@pytest.fixture
def verification_token() -> str:
    """Create test verification token."""
    return "test_verification_token_12345"


@pytest.fixture
def password_reset_token() -> str:
    """Create test password reset token."""
    return "test_reset_token_12345"


async def test_app_email_service_initialization(mailer: EmailService) -> None:
    """Test AppEmailService initialization."""
    service = AppEmailService(mailer=mailer)

    assert service.base_url is not None
    assert service.app_name is not None


async def test_app_email_service_settings_integration(app_email_service: AppEmailService) -> None:
    """Test AppEmailService gets settings correctly."""
    assert isinstance(app_email_service.base_url, str)
    assert isinstance(app_email_service.app_name, str)


async def test_send_verification_email_with_name(
    app_email_service: AppEmailService,
    user: m.User,
    verification_token: str,
) -> None:
    """Test sending verification email to user with name."""
    result = await app_email_service.send_verification_email(cast("UserProtocol", user), verification_token)

    assert result is True
    assert len(InMemoryBackend.outbox) == 1
    message = InMemoryBackend.outbox[0]
    assert user.email in message.to
    assert "verify" in message.subject.lower()


async def test_send_verification_email_without_name(
    app_email_service: AppEmailService,
    user_without_name: m.User,
    verification_token: str,
) -> None:
    """Test sending verification email to user without name."""
    result = await app_email_service.send_verification_email(
        cast("UserProtocol", user_without_name), verification_token
    )

    assert result is True
    assert len(InMemoryBackend.outbox) == 1


async def test_send_verification_email_url_construction(
    app_email_service: AppEmailService,
    user: m.User,
    verification_token: str,
) -> None:
    """Test verification email URL construction."""
    expected_url = f"{app_email_service.base_url}/verify-email?token={verification_token}"

    html = app_email_service._render_template(
        "email-verification.html",
        {
            "USER_NAME": user.name or "there",
            "VERIFICATION_URL": expected_url,
            "EXPIRES_HOURS": 24,
        },
    )

    assert expected_url in html


async def test_send_welcome_email(
    app_email_service: AppEmailService,
    user: m.User,
) -> None:
    """Test sending welcome email."""
    result = await app_email_service.send_welcome_email(cast("UserProtocol", user))

    assert result is True
    assert len(InMemoryBackend.outbox) == 1
    message = InMemoryBackend.outbox[0]
    assert "welcome" in message.subject.lower()


async def test_send_password_reset_email(
    app_email_service: AppEmailService,
    user: m.User,
    password_reset_token: str,
) -> None:
    """Test sending password reset email."""
    result = await app_email_service.send_password_reset_email(
        cast("UserProtocol", user),
        password_reset_token,
        expires_in_minutes=60,
    )

    assert result is True
    assert len(InMemoryBackend.outbox) == 1
    message = InMemoryBackend.outbox[0]
    assert "reset" in message.subject.lower()


async def test_send_password_reset_confirmation_email(
    app_email_service: AppEmailService,
    user: m.User,
) -> None:
    """Test sending password reset confirmation email."""
    result = await app_email_service.send_password_reset_confirmation_email(cast("UserProtocol", user))

    assert result is True
    assert len(InMemoryBackend.outbox) == 1


async def test_send_team_invitation_email(
    app_email_service: AppEmailService,
) -> None:
    """Test sending team invitation email."""
    result = await app_email_service.send_team_invitation_email(
        invitee_email="invitee@example.com",
        inviter_name="Inviter User",
        team_name="Test Team",
        invitation_url="http://localhost:8000/accept-invite?token=abc123",
    )

    assert result is True
    assert len(InMemoryBackend.outbox) == 1
    message = InMemoryBackend.outbox[0]
    assert "invitee@example.com" in message.to
    assert "Test Team" in message.subject


async def test_verification_email_content_structure(
    app_email_service: AppEmailService,
    user: m.User,
    verification_token: str,
) -> None:
    """Test that verification email content has proper structure."""
    verification_url = f"{app_email_service.base_url}/verify-email?token={verification_token}"
    html = app_email_service._render_template(
        "email-verification.html",
        {
            "USER_NAME": user.name or "there",
            "VERIFICATION_URL": verification_url,
            "EXPIRES_HOURS": 24,
        },
    )

    assert "verify your email" in html.lower()
    assert verification_url in html
    assert ">24<" in html or "24" in html
    assert "hours" in html.lower()
    assert app_email_service.app_name in html


async def test_verification_email_security_considerations(
    app_email_service: AppEmailService,
    user: m.User,
    verification_token: str,
) -> None:
    """Test security-related aspects of verification email."""
    verification_url = f"{app_email_service.base_url}/verify-email?token={verification_token}"
    html = app_email_service._render_template(
        "email-verification.html",
        {
            "USER_NAME": user.name or "there",
            "VERIFICATION_URL": verification_url,
            "EXPIRES_HOURS": 24,
        },
    )

    # Note: HTML escapes apostrophes as &#x27; and may have line breaks in text
    assert "didn't create an account" in html.lower() or "didn&#x27;t create an account" in html.lower()
    assert "safely ignore" in html.lower()
    assert "expire" in html.lower()


async def test_html_to_text_conversion(
    app_email_service: AppEmailService,
) -> None:
    """Test HTML to plain text conversion."""
    html = "<p>Hello <strong>World</strong></p>&nbsp;<a href='test'>Link</a>"

    text = app_email_service._html_to_text(html)

    assert "<" not in text
    assert ">" not in text
    assert "Hello" in text
    assert "World" in text
    assert "Link" in text


async def test_template_rendering(
    app_email_service: AppEmailService,
) -> None:
    """Test email template rendering."""
    html = app_email_service._render_template(
        "welcome.html",
        {"USER_NAME": "Test User", "LOGIN_URL": "https://example.com/login"},
    )

    assert "Test User" in html
    assert "https://example.com/login" in html
    assert app_email_service.app_name in html


async def test_template_caching(
    app_email_service: AppEmailService,
) -> None:
    """Test that templates are cached after first load."""
    # First render loads the template
    app_email_service._render_template(
        "welcome.html",
        {"USER_NAME": "User1", "LOGIN_URL": "https://example.com/login"},
    )

    # Verify cache contains the template
    assert "welcome.html" in app_email_service._template_cache

    # Second render should use cached version
    html2 = app_email_service._render_template(
        "welcome.html",
        {"USER_NAME": "User2", "LOGIN_URL": "https://example.com/login"},
    )

    assert "User2" in html2
