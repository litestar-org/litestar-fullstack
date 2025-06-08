"""Unit tests for email service functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.db.models.email_verification_token import EmailVerificationToken
from app.db.models.user import User
from app.lib.email import EmailService


class TestEmailService:
    """Test EmailService functionality."""

    @pytest.fixture
    def email_service(self) -> EmailService:
        """Create EmailService instance."""
        return EmailService()

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
    def verification_token(self, user: User) -> EmailVerificationToken:
        """Create test verification token."""
        return EmailVerificationToken(
            user_id=user.id,
            token="test_verification_token_12345",
            email=user.email,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )

    def test_email_service_initialization(self) -> None:
        """Test EmailService initialization."""
        # Arrange & Act
        service = EmailService()

        # Assert
        assert service.base_url is not None
        assert service.app_name is not None
        assert service.settings is not None

    def test_email_service_settings_integration(self) -> None:
        """Test EmailService gets settings correctly."""
        # Arrange & Act
        service = EmailService()

        # Assert
        assert hasattr(service, 'settings')
        assert hasattr(service, 'app_settings')
        assert hasattr(service, 'base_url')
        assert hasattr(service, 'app_name')

    @patch("app.lib.email.logger")
    async def test_send_verification_email_with_name(
        self,
        mock_logger,
        email_service: EmailService,
        user: User,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test sending verification email to user with name."""
        # Act
        await email_service.send_verification_email(user, verification_token)

        # Assert
        expected_url = f"{email_service.base_url}/verify-email?token={verification_token.token}"

        # Verify logger calls
        mock_logger.info.assert_any_call(
            "Email verification sent to %s. Verification URL: %s",
            user.email,
            expected_url,
        )

        # Verify email content was logged
        assert mock_logger.info.call_count == 2
        email_content_call = mock_logger.info.call_args_list[1]
        email_content = email_content_call[0][1]

        assert "Test User" in email_content
        assert expected_url in email_content
        assert "24 hours" in email_content

    @patch("app.lib.email.logger")
    async def test_send_verification_email_without_name(
        self,
        mock_logger,
        email_service: EmailService,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test sending verification email to user without name."""
        # Arrange
        user = User(
            id=uuid4(),
            email="noname@example.com",
            name=None,  # No name provided
            is_active=True,
            is_verified=False,
            is_superuser=False,
            login_count=0,
        )

        # Act
        await email_service.send_verification_email(user, verification_token)

        # Assert
        expected_url = f"{email_service.base_url}/verify-email?token={verification_token.token}"

        # Verify logger calls
        mock_logger.info.assert_any_call(
            "Email verification sent to %s. Verification URL: %s",
            user.email,
            expected_url,
        )

        # Verify email content was logged and contains "there" instead of name
        email_content_call = mock_logger.info.call_args_list[1]
        email_content = email_content_call[0][1]

        assert "Hi there," in email_content
        assert expected_url in email_content

    @patch("app.lib.email.logger")
    async def test_send_verification_email_url_construction(
        self,
        mock_logger,
        user: User,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test verification email URL construction with different base URLs."""
        # Arrange
        custom_service = EmailService(base_url="https://myapp.production.com")

        # Act
        await custom_service.send_verification_email(user, verification_token)

        # Assert
        expected_url = f"https://myapp.production.com/verify-email?token={verification_token.token}"
        mock_logger.info.assert_any_call(
            "Email verification sent to %s. Verification URL: %s",
            user.email,
            expected_url,
        )

    @patch("app.lib.email.logger")
    async def test_send_welcome_email(
        self,
        mock_logger,
        email_service: EmailService,
        user: User,
    ) -> None:
        """Test sending welcome email."""
        # Act
        await email_service.send_welcome_email(user)

        # Assert
        mock_logger.info.assert_called_once_with("Welcome email would be sent to %s", user.email)

    async def test_verification_email_content_structure(
        self,
        email_service: EmailService,
        user: User,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test that verification email content has proper structure."""
        # We'll capture the log output to verify email content structure
        with patch("app.lib.email.logger") as mock_logger:
            # Act
            await email_service.send_verification_email(user, verification_token)

            # Assert - verify email content structure
            email_content_call = mock_logger.info.call_args_list[1]
            email_content = email_content_call[0][1]

            # Check for required elements
            assert "Please verify your email address" in email_content
            assert "clicking the link below" in email_content
            assert f"/verify-email?token={verification_token.token}" in email_content
            assert "24 hours" in email_content
            assert "ignore this email" in email_content
            assert "Your App Team" in email_content

    async def test_verification_email_security_considerations(
        self,
        email_service: EmailService,
        user: User,
        verification_token: EmailVerificationToken,
    ) -> None:
        """Test security-related aspects of verification email."""
        with patch("app.lib.email.logger") as mock_logger:
            # Act
            await email_service.send_verification_email(user, verification_token)

            # Assert - check security messaging
            email_content_call = mock_logger.info.call_args_list[1]
            email_content = email_content_call[0][1]

            # Should include security guidance
            assert "didn't create an account" in email_content
            assert "ignore this email" in email_content

            # Should include expiration information
            assert "expire" in email_content
