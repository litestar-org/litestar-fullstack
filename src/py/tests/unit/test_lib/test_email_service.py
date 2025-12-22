"""Unit tests for email service functionality."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest

from app.db.models.email_verification_token import EmailVerificationToken
from app.db.models.password_reset_token import PasswordResetToken
from app.db.models.user import User
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
    def user(self) -> User:
        """Create test user."""
        return User(
            id=uuid4(),
            email="test@example.com",
            name="Test User",
            is_active=True,
            is_verified=False,
            is_superuser=False,
            login_count=0,
        )

    @pytest.fixture
    def user_without_name(self) -> User:
        """Create test user without name."""
        return User(
            id=uuid4(),
            email="noname@example.com",
            name=None,
            is_active=True,
            is_verified=False,
            is_superuser=False,
            login_count=0,
        )

    @pytest.fixture
    def verification_token(self, user: User) -> EmailVerificationToken:
        """Create test verification token."""
        return EmailVerificationToken(
            user_id=user.id,
            token="test_verification_token_12345",
            email=user.email,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )

    @pytest.fixture
    def password_reset_token(self, user: User) -> PasswordResetToken:
        """Create test password reset token."""
        return PasswordResetToken(
            user_id=user.id,
            token="test_reset_token_12345",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            ip_address="127.0.0.1",
            user_agent="Test Agent",
        )

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
        user: User,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test sending verification email to user with name."""
        # Act
        result = await email_service.send_verification_email(cast("UserProtocol", user), verification_token)

        # Assert - email is disabled by default so returns False
        assert result is False

    async def test_send_verification_email_without_name(
        self,
        email_service: EmailService,
        user_without_name: User,
        verification_token: EmailVerificationToken,
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
        user: User,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test verification email URL construction."""
        # The base URL comes from settings
        expected_url = f"{email_service.base_url}/verify-email?token={verification_token.token}"

        # Act - generate the HTML to verify URL is correct
        html = email_service._generate_verification_html(
            user_name=user.name or "there",
            verification_url=expected_url,
        )

        # Assert
        assert expected_url in html

    async def test_send_welcome_email(
        self,
        email_service: EmailService,
        user: User,
    ) -> None:
        """Test sending welcome email."""
        # Act
        result = await email_service.send_welcome_email(cast("UserProtocol", user))

        # Assert
        assert result is False  # Email disabled by default

    async def test_send_password_reset_email(
        self,
        email_service: EmailService,
        user: User,
        password_reset_token: PasswordResetToken,
    ) -> None:
        """Test sending password reset email."""
        # Act
        result = await email_service.send_password_reset_email(
            cast("UserProtocol", user),
            password_reset_token,
            expires_in_minutes=60,
            ip_address="192.168.1.1",
        )

        # Assert
        assert result is False  # Email disabled by default

    async def test_send_password_reset_confirmation_email(
        self,
        email_service: EmailService,
        user: User,
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
        user: User,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test that verification email content has proper structure."""
        # Act - generate HTML content
        verification_url = f"{email_service.base_url}/verify-email?token={verification_token.token}"
        html = email_service._generate_verification_html(
            user_name=user.name or "there",
            verification_url=verification_url,
        )

        # Assert - check for required elements
        assert "verify your email" in html.lower()
        assert verification_url in html
        assert "24 hours" in html
        assert email_service.app_name in html

    async def test_verification_email_security_considerations(
        self,
        email_service: EmailService,
        user: User,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test security-related aspects of verification email."""
        # Act - generate HTML content
        verification_url = f"{email_service.base_url}/verify-email?token={verification_token.token}"
        html = email_service._generate_verification_html(
            user_name=user.name or "there",
            verification_url=verification_url,
        )

        # Assert - check security messaging
        assert "didn't create an account" in html.lower()
        assert "ignore this email" in html.lower()
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

    def test_generate_base_html(
        self,
        email_service: EmailService,
    ) -> None:
        """Test base HTML template generation."""
        # Act
        html = email_service._generate_base_html("<p>Content</p>")

        # Assert
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "<body" in html
        assert email_service.app_name in html
        assert "<p>Content</p>" in html
