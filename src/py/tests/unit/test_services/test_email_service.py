"""Tests for the email service with backend abstraction."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.db import models as m
from app.lib.email import EmailService, get_backend
from app.lib.email.backends.locmem import InMemoryBackend
from app.lib.email.base import EmailMessage, EmailMultiAlternatives


@pytest.fixture(autouse=True)
def clear_outbox():
    """Clear in-memory backend outbox before each test."""
    InMemoryBackend.clear()
    yield
    InMemoryBackend.clear()


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock(spec=m.User)
    user.email = "user@test.com"
    user.name = "Test User"
    return user


@pytest.fixture
def mock_verification_token():
    """Create a mock verification token."""
    return "test-verification-token-123"


@pytest.fixture
def mock_reset_token():
    """Create a mock password reset token."""
    return "test-reset-token-456"


class TestEmailMessage:
    """Test EmailMessage dataclass."""

    def test_create_email_message(self):
        """Test creating an EmailMessage."""
        message = EmailMessage(
            subject="Test Subject",
            body="Test body",
            from_email="sender@test.com",
            to=["recipient@test.com"],
        )

        assert message.subject == "Test Subject"
        assert message.body == "Test body"
        assert message.from_email == "sender@test.com"
        assert message.to == ["recipient@test.com"]
        assert message.cc == []
        assert message.bcc == []
        assert message.reply_to == []

    def test_email_message_with_all_fields(self):
        """Test EmailMessage with all optional fields."""
        message = EmailMessage(
            subject="Full Test",
            body="Body content",
            from_email="sender@test.com",
            to=["to@test.com"],
            cc=["cc@test.com"],
            bcc=["bcc@test.com"],
            reply_to=["reply@test.com"],
            headers={"X-Custom": "header"},
        )

        assert message.cc == ["cc@test.com"]
        assert message.bcc == ["bcc@test.com"]
        assert message.reply_to == ["reply@test.com"]
        assert message.headers == {"X-Custom": "header"}


class TestEmailMultiAlternatives:
    """Test EmailMultiAlternatives dataclass."""

    def test_create_multi_alternatives(self):
        """Test creating EmailMultiAlternatives."""
        message = EmailMultiAlternatives(
            subject="HTML Email",
            body="Plain text body",
            html_body="<p>HTML body</p>",
            from_email="sender@test.com",
            to=["recipient@test.com"],
        )

        assert message.subject == "HTML Email"
        assert message.body == "Plain text body"
        assert message.html_body == "<p>HTML body</p>"


class TestInMemoryBackend:
    """Test InMemoryBackend for testing purposes."""

    async def test_send_stores_messages(self):
        """Test that send stores messages in outbox."""
        backend = InMemoryBackend()
        message = EmailMessage(
            subject="Test",
            body="Body",
            from_email="from@test.com",
            to=["to@test.com"],
        )

        count = await backend.send_messages([message])

        assert count == 1
        assert len(InMemoryBackend.outbox) == 1
        assert InMemoryBackend.outbox[0].subject == "Test"

    async def test_clear_outbox(self):
        """Test clearing the outbox."""
        backend = InMemoryBackend()
        message = EmailMessage(
            subject="Test",
            body="Body",
            from_email="from@test.com",
            to=["to@test.com"],
        )

        await backend.send_messages([message])
        assert len(InMemoryBackend.outbox) == 1

        InMemoryBackend.clear()
        assert len(InMemoryBackend.outbox) == 0


class TestEmailService:
    """Test cases for EmailService."""

    def test_init(self):
        """Test email service initialization."""
        service = EmailService()

        assert service.fail_silently is False
        assert service.base_url is not None
        assert service.app_name is not None

    def test_init_with_fail_silently(self):
        """Test email service initialization with fail_silently."""
        service = EmailService(fail_silently=True)

        assert service.fail_silently is True

    def test_html_to_text(self):
        """Test HTML to text conversion."""
        service = EmailService()

        html = "<p>Hello <strong>World</strong></p>"
        text = service._html_to_text(html)

        assert "<" not in text
        assert ">" not in text
        assert "Hello" in text
        assert "World" in text

    def test_html_to_text_entities(self):
        """Test HTML entity conversion."""
        service = EmailService()

        html = "&nbsp;&amp;&lt;&gt;&quot;"
        text = service._html_to_text(html)

        assert "&" in text
        assert "<" in text
        assert ">" in text
        assert '"' in text

    def test_render_welcome_template(self):
        """Test welcome email template rendering."""
        service = EmailService()

        html = service._render_template(
            "welcome.html",
            {"USER_NAME": "Test User", "LOGIN_URL": "http://test.com/login"},
        )

        assert "Test User" in html
        assert "http://test.com/login" in html
        assert service.app_name in html

    def test_render_verification_template(self):
        """Test verification email template rendering."""
        service = EmailService()

        html = service._render_template(
            "email-verification.html",
            {
                "USER_NAME": "Test User",
                "VERIFICATION_URL": "http://test.com/verify?token=abc",
                "EXPIRES_HOURS": 24,
            },
        )

        assert "Test User" in html
        assert "http://test.com/verify?token=abc" in html
        assert "verify" in html.lower()

    def test_render_password_reset_template(self):
        """Test password reset email template rendering."""
        service = EmailService()

        html = service._render_template(
            "password-reset.html",
            {
                "USER_NAME": "Test User",
                "RESET_URL": "http://test.com/reset?token=abc",
                "EXPIRES_MINUTES": 60,
            },
        )

        assert "Test User" in html
        assert "http://test.com/reset?token=abc" in html
        assert "60" in html

    def test_render_team_invitation_template(self):
        """Test team invitation email template rendering."""
        service = EmailService()

        html = service._render_template(
            "team-invitation.html",
            {
                "INVITER_NAME": "John Doe",
                "TEAM_NAME": "Test Team",
                "INVITATION_URL": "http://test.com/invite?token=abc",
            },
        )

        assert "John Doe" in html
        assert "Test Team" in html
        assert "http://test.com/invite?token=abc" in html

    @pytest.mark.asyncio
    async def test_send_email_disabled(self):
        """Test sending email when service is disabled."""
        service = EmailService()

        result = await service.send_email(
            to_email="test@test.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

        # Email is disabled by default in tests
        assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_email(self, mock_user, mock_verification_token):
        """Test sending verification email."""
        service = EmailService()

        result = await service.send_verification_email(mock_user, mock_verification_token)

        # Email is disabled by default
        assert result is False

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, mock_user):
        """Test sending welcome email."""
        service = EmailService()

        result = await service.send_welcome_email(mock_user)

        assert result is False  # Email disabled by default

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, mock_user, mock_reset_token):
        """Test sending password reset email."""
        service = EmailService()

        result = await service.send_password_reset_email(
            mock_user,
            mock_reset_token,
            expires_in_minutes=60,
        )

        assert result is False  # Email disabled by default

    @pytest.mark.asyncio
    async def test_send_password_reset_confirmation_email(self, mock_user):
        """Test sending password reset confirmation email."""
        service = EmailService()

        result = await service.send_password_reset_confirmation_email(mock_user)

        assert result is False  # Email disabled by default

    @pytest.mark.asyncio
    async def test_send_team_invitation_email(self):
        """Test sending team invitation email."""
        service = EmailService()

        result = await service.send_team_invitation_email(
            invitee_email="invitee@test.com",
            inviter_name="John Doe",
            team_name="Test Team",
            invitation_url="https://app.test.com/invite/abc123",
        )

        assert result is False  # Email disabled by default


class TestGetBackend:
    """Test get_backend function."""

    def test_get_backend_returns_instance(self):
        """Test that get_backend returns a backend instance."""
        # Default backend (console) should be returned
        backend = get_backend()

        assert backend is not None
        assert hasattr(backend, "send_messages")

    def test_get_backend_with_fail_silently(self):
        """Test get_backend with fail_silently option."""
        backend = get_backend(fail_silently=True)

        assert backend.fail_silently is True

    def test_inmemory_backend_class(self):
        """Test InMemoryBackend class directly."""
        backend = InMemoryBackend()

        assert hasattr(backend, "send_messages")
        assert hasattr(backend, "outbox")
