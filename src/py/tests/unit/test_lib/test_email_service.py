"""Unit tests for email service functionality."""

from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest

from app.db import models as m
from app.lib.email import EmailService
from app.lib.email.backends.locmem import InMemoryBackend

if TYPE_CHECKING:
    from app.lib.email.service import UserProtocol


class TestEmailService:
    """Test EmailService functionality."""

    @pytest.fixture(autouse=True)
    def setup_test_backend(self) -> None:
        """Configure test email backend and clear outbox."""
        InMemoryBackend.clear()

    @pytest.fixture
    def email_service(self) -> EmailService:
        """Create EmailService instance."""
        return EmailService(fail_silently=False)

    @pytest.fixture
    def user(self) -> m.User:
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
    def user_without_name(self) -> m.User:
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
    def verification_token(self) -> str:
        """Create test verification token."""
        return "test_verification_token_12345"

    @pytest.fixture
    def password_reset_token(self) -> str:
        """Create test password reset token."""
        return "test_reset_token_12345"

    def test_email_service_initialization(self) -> None:
        """Test EmailService initialization."""
        # Arrange & Act
        service = EmailService()

        # Assert
        assert service.base_url is not None
        assert service.app_name is not None
        assert service.fail_silently is False

    def test_email_service_fail_silently(self) -> None:
        """Test EmailService with fail_silently option."""
        # Arrange & Act
        service = EmailService(fail_silently=True)

        # Assert
        assert service.fail_silently is True

    def test_email_service_settings_integration(self) -> None:
        """Test EmailService gets settings correctly."""
        # Arrange & Act
        service = EmailService()

        # Assert - check properties work
        assert isinstance(service.base_url, str)
        assert isinstance(service.app_name, str)

    async def test_send_verification_email_with_name(
        self,
        email_service: EmailService,
        user: m.User,
        verification_token: str,
    ) -> None:
        """Test sending verification email to user with name."""
        # Act
        result = await email_service.send_verification_email(cast("UserProtocol", user), verification_token)

        # Assert - email is disabled by default so returns False
        assert result is False

    async def test_send_verification_email_without_name(
        self,
        email_service: EmailService,
        user_without_name: m.User,
        verification_token: str,
    ) -> None:
        """Test sending verification email to user without name."""
        # Act
        result = await email_service.send_verification_email(
            cast("UserProtocol", user_without_name), verification_token
        )

        # Assert
        assert result is False  # Email disabled by default

    async def test_send_verification_email_url_construction(
        self,
        email_service: EmailService,
        user: m.User,
        verification_token: str,
    ) -> None:
        """Test verification email URL construction."""
        # The base URL comes from settings
        expected_url = f"{email_service.base_url}/verify-email?token={verification_token}"

        html = email_service._render_template(
            "email-verification.html",
            {
                "USER_NAME": user.name or "there",
                "VERIFICATION_URL": expected_url,
                "EXPIRES_HOURS": 24,
            },
        )

        # Assert
        assert expected_url in html

    async def test_send_welcome_email(
        self,
        email_service: EmailService,
        user: m.User,
    ) -> None:
        """Test sending welcome email."""
        # Act
        result = await email_service.send_welcome_email(cast("UserProtocol", user))

        # Assert
        assert result is False  # Email disabled by default

    async def test_send_password_reset_email(
        self,
        email_service: EmailService,
        user: m.User,
        password_reset_token: str,
    ) -> None:
        """Test sending password reset email."""
        # Act
        result = await email_service.send_password_reset_email(
            cast("UserProtocol", user),
            password_reset_token,
            expires_in_minutes=60,
        )

        # Assert
        assert result is False  # Email disabled by default

    async def test_send_password_reset_confirmation_email(
        self,
        email_service: EmailService,
        user: m.User,
    ) -> None:
        """Test sending password reset confirmation email."""
        # Act
        result = await email_service.send_password_reset_confirmation_email(cast("UserProtocol", user))

        # Assert
        assert result is False  # Email disabled by default

    async def test_send_team_invitation_email(
        self,
        email_service: EmailService,
    ) -> None:
        """Test sending team invitation email."""
        # Act
        result = await email_service.send_team_invitation_email(
            invitee_email="invitee@example.com",
            inviter_name="Inviter User",
            team_name="Test Team",
            invitation_url="http://localhost:8000/accept-invite?token=abc123",
        )

        # Assert
        assert result is False  # Email disabled by default

    async def test_verification_email_content_structure(
        self,
        email_service: EmailService,
        user: m.User,
        verification_token: str,
    ) -> None:
        """Test that verification email content has proper structure."""
        # Act - generate HTML content
        verification_url = f"{email_service.base_url}/verify-email?token={verification_token}"
        html = email_service._render_template(
            "email-verification.html",
            {
                "USER_NAME": user.name or "there",
                "VERIFICATION_URL": verification_url,
                "EXPIRES_HOURS": 24,
            },
        )

        # Assert - check for required elements
        assert "verify your email" in html.lower()
        assert verification_url in html
        # React email templates insert HTML comments between interpolated values,
        # so check for "24" and "hours" separately rather than "24 hours" together
        assert ">24<" in html or "24" in html
        assert "hours" in html.lower()
        assert email_service.app_name in html

    async def test_verification_email_security_considerations(
        self,
        email_service: EmailService,
        user: m.User,
        verification_token: str,
    ) -> None:
        """Test security-related aspects of verification email."""
        # Act - generate HTML content
        verification_url = f"{email_service.base_url}/verify-email?token={verification_token}"
        html = email_service._render_template(
            "email-verification.html",
            {
                "USER_NAME": user.name or "there",
                "VERIFICATION_URL": verification_url,
                "EXPIRES_HOURS": 24,
            },
        )

        # Assert - check security messaging
        # Note: HTML escapes apostrophes as &#x27; and may have line breaks in text
        assert "didn't create an account" in html.lower() or "didn&#x27;t create an account" in html.lower()
        assert "safely ignore" in html.lower()
        assert "expire" in html.lower()

    def test_html_to_text_conversion(
        self,
        email_service: EmailService,
    ) -> None:
        """Test HTML to plain text conversion."""
        # Arrange
        html = "<p>Hello <strong>World</strong></p>&nbsp;<a href='test'>Link</a>"

        # Act
        text = email_service._html_to_text(html)

        # Assert
        assert "<" not in text
        assert ">" not in text
        assert "Hello" in text
        assert "World" in text
        assert "Link" in text

    def test_template_rendering(
        self,
        email_service: EmailService,
    ) -> None:
        """Test email template rendering."""
        html = email_service._render_template(
            "welcome.html",
            {"USER_NAME": "Test User", "LOGIN_URL": "https://example.com/login"},
        )

        assert "Test User" in html
        assert "https://example.com/login" in html
        assert email_service.app_name in html
