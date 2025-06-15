"""Tests for the email service."""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.db.models import EmailVerificationToken, PasswordResetToken, User
from app.lib.email import EmailService


@pytest.fixture
def mock_settings():
    """Mock settings for email service."""
    with patch("app.lib.email.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.email.ENABLED = True
        mock_settings.email.SMTP_HOST = "smtp.test.com"
        mock_settings.email.SMTP_PORT = 587
        mock_settings.email.SMTP_USER = "test@test.com"
        mock_settings.email.SMTP_PASSWORD = "testpass"
        mock_settings.email.USE_TLS = True
        mock_settings.email.USE_SSL = False
        mock_settings.email.FROM_EMAIL = "noreply@test.com"
        mock_settings.email.FROM_NAME = "Test App"
        mock_settings.email.TIMEOUT = 30
        mock_settings.app.URL = "https://app.test.com"
        mock_settings.app.NAME = "Test App"
        mock_settings.vite.TEMPLATE_DIR = "/templates"
        mock_get_settings.return_value = mock_settings
        yield mock_settings


@pytest.fixture
def email_service(mock_settings):
    """Create email service with mocked settings."""
    return EmailService()


@pytest.fixture
def mock_smtp():
    """Mock SMTP connection."""
    with patch("app.lib.email.smtplib.SMTP") as mock_smtp_class:
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        yield mock_smtp


@pytest.fixture
def mock_smtp_ssl():
    """Mock SMTP SSL connection."""
    with patch("app.lib.email.smtplib.SMTP_SSL") as mock_smtp_ssl_class:
        mock_smtp_ssl = Mock()
        mock_smtp_ssl_class.return_value = mock_smtp_ssl
        yield mock_smtp_ssl


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock(spec=User)
    user.email = "user@test.com"
    user.name = "Test User"
    return user


@pytest.fixture
def mock_verification_token():
    """Create a mock verification token."""
    token = Mock(spec=EmailVerificationToken)
    token.token = "test-verification-token-123"
    return token


@pytest.fixture
def mock_reset_token():
    """Create a mock password reset token."""
    token = Mock(spec=PasswordResetToken)
    token.token = "test-reset-token-456"
    return token


class TestEmailService:
    """Test cases for EmailService."""

    def test_init(self, email_service, mock_settings):
        """Test email service initialization."""
        assert email_service.settings == mock_settings.email
        assert email_service.app_settings == mock_settings.app
        assert email_service.base_url == "https://app.test.com"
        assert email_service.app_name == "Test App"

    def test_create_smtp_connection_disabled(self, mock_settings):
        """Test SMTP connection when email is disabled."""
        mock_settings.email.ENABLED = False
        service = EmailService()

        result = service._create_smtp_connection()

        assert result is None

    def test_create_smtp_connection_tls(self, email_service, mock_smtp):
        """Test SMTP connection with TLS."""
        email_service.settings.USE_SSL = False
        email_service.settings.USE_TLS = True

        result = email_service._create_smtp_connection()

        assert result == mock_smtp
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@test.com", "testpass")

    def test_create_smtp_connection_ssl(self, mock_settings, mock_smtp_ssl):
        """Test SMTP connection with SSL."""
        mock_settings.email.USE_SSL = True
        mock_settings.email.USE_TLS = False
        service = EmailService()

        result = service._create_smtp_connection()

        assert result == mock_smtp_ssl
        mock_smtp_ssl.login.assert_called_once_with("test@test.com", "testpass")

    def test_create_smtp_connection_error(self, email_service):
        """Test SMTP connection error handling."""
        with patch("app.lib.email.smtplib.SMTP", side_effect=Exception("Connection failed")):
            result = email_service._create_smtp_connection()

            assert result is None

    @pytest.mark.asyncio
    async def test_send_email_disabled(self, mock_settings):
        """Test sending email when service is disabled."""
        mock_settings.email.ENABLED = False
        service = EmailService()

        result = await service.send_email(to_email="test@test.com", subject="Test", html_content="<p>Test</p>")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_success(self, email_service, mock_smtp):
        """Test successful email sending."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)

        result = await email_service.send_email(
            to_email="recipient@test.com",
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            text_content="Test Text",
        )

        assert result is True
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_multiple_recipients(self, email_service, mock_smtp):
        """Test sending email to multiple recipients."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)
        recipients = ["user1@test.com", "user2@test.com"]

        result = await email_service.send_email(to_email=recipients, subject="Test Subject", html_content="<p>Test</p>")

        assert result is True
        mock_smtp.send_message.assert_called_once()
        # Check that to_addrs contains all recipients
        call_args = mock_smtp.send_message.call_args
        assert call_args[1]["to_addrs"] == recipients

    @pytest.mark.asyncio
    async def test_send_email_with_reply_to(self, email_service, mock_smtp):
        """Test sending email with reply-to header."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)

        result = await email_service.send_email(
            to_email="recipient@test.com", subject="Test Subject", html_content="<p>Test</p>", reply_to="reply@test.com"
        )

        assert result is True
        # Verify the message was created with reply-to
        call_args = mock_smtp.send_message.call_args[0][0]
        assert call_args["Reply-To"] == "reply@test.com"

    @pytest.mark.asyncio
    async def test_send_email_auto_text_generation(self, email_service, mock_smtp):
        """Test automatic text content generation from HTML."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)

        result = await email_service.send_email(
            to_email="recipient@test.com",
            subject="Test Subject",
            html_content="<p>Test <strong>HTML</strong> content</p>",
        )

        assert result is True
        # Verify text was auto-generated by checking the message parts
        call_args = mock_smtp.send_message.call_args[0][0]
        assert isinstance(call_args, MIMEMultipart)

    @pytest.mark.asyncio
    async def test_send_email_connection_failure(self, email_service):
        """Test email sending when connection fails."""
        email_service._create_smtp_connection = Mock(return_value=None)

        result = await email_service.send_email(
            to_email="recipient@test.com", subject="Test Subject", html_content="<p>Test</p>"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_send_failure(self, email_service, mock_smtp):
        """Test email sending when send_message fails."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)
        mock_smtp.send_message.side_effect = Exception("Send failed")

        result = await email_service.send_email(
            to_email="recipient@test.com", subject="Test Subject", html_content="<p>Test</p>"
        )

        assert result is False
        mock_smtp.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_template_email_success(self, email_service, mock_smtp):
        """Test sending template email."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)

        # Mock Jinja2 template loading
        mock_html_template = Mock()
        mock_html_template.render.return_value = "<p>Rendered HTML</p>"
        mock_text_template = Mock()
        mock_text_template.render.return_value = "Rendered Text"

        email_service.jinja_env.get_template = Mock(side_effect=[mock_html_template, mock_text_template])

        result = await email_service.send_template_email(
            template_name="test_template",
            to_email="recipient@test.com",
            subject="Test Subject",
            context={"name": "Test User"},
        )

        assert result is True
        email_service.jinja_env.get_template.assert_any_call("emails/test_template.html.j2")
        email_service.jinja_env.get_template.assert_any_call("emails/test_template.txt.j2")
        mock_html_template.render.assert_called_once_with(name="Test User")
        mock_text_template.render.assert_called_once_with(name="Test User")

    @pytest.mark.asyncio
    async def test_send_template_email_no_text_template(self, email_service, mock_smtp):
        """Test sending template email without text template."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)

        # Mock Jinja2 template loading
        mock_html_template = Mock()
        mock_html_template.render.return_value = "<p>Rendered HTML</p>"

        def get_template_side_effect(template_name):
            if "html" in template_name:
                return mock_html_template
            raise Exception("Text template not found")

        email_service.jinja_env.get_template = Mock(side_effect=get_template_side_effect)

        result = await email_service.send_template_email(
            template_name="test_template",
            to_email="recipient@test.com",
            subject="Test Subject",
            context={"name": "Test User"},
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_template_email_error(self, email_service):
        """Test template email error handling."""
        email_service.jinja_env.get_template = Mock(side_effect=Exception("Template error"))

        result = await email_service.send_template_email(
            template_name="test_template", to_email="recipient@test.com", subject="Test Subject", context={}
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_email_with_template(
        self, email_service, mock_user, mock_verification_token, mock_smtp
    ):
        """Test sending verification email with template."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)

        # Mock successful template sending
        email_service.send_template_email = AsyncMock(return_value=True)

        result = await email_service.send_verification_email(mock_user, mock_verification_token)

        assert result is True
        email_service.send_template_email.assert_called_once()
        call_args = email_service.send_template_email.call_args
        assert call_args[1]["template_name"] == "email_verification"
        assert call_args[1]["to_email"] == "user@test.com"
        assert "Verify your email address" in call_args[1]["subject"]
        assert (
            call_args[1]["context"]["verification_url"]
            == "https://app.test.com/verify-email?token=test-verification-token-123"
        )

    @pytest.mark.asyncio
    async def test_send_verification_email_fallback(self, email_service, mock_user, mock_verification_token, mock_smtp):
        """Test sending verification email with fallback."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)

        # Mock template sending failure to trigger fallback
        email_service.send_template_email = AsyncMock(side_effect=Exception("Template error"))

        result = await email_service.send_verification_email(mock_user, mock_verification_token)

        assert result is True
        mock_smtp.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, email_service, mock_user, mock_smtp):
        """Test sending welcome email."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)
        email_service.send_template_email = AsyncMock(return_value=True)

        result = await email_service.send_welcome_email(mock_user)

        assert result is True
        email_service.send_template_email.assert_called_once()
        call_args = email_service.send_template_email.call_args
        assert call_args[1]["template_name"] == "welcome"
        assert call_args[1]["to_email"] == "user@test.com"
        assert "Welcome to" in call_args[1]["subject"]

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, email_service, mock_user, mock_reset_token, mock_smtp):
        """Test sending password reset email."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)
        email_service.send_template_email = AsyncMock(return_value=True)

        result = await email_service.send_password_reset_email(
            mock_user, mock_reset_token, expires_in_minutes=60, ip_address="192.168.1.1"
        )

        assert result is True
        email_service.send_template_email.assert_called_once()
        call_args = email_service.send_template_email.call_args
        assert call_args[1]["template_name"] == "password_reset"
        assert call_args[1]["context"]["reset_url"] == "https://app.test.com/reset-password?token=test-reset-token-456"
        assert call_args[1]["context"]["expires_in_minutes"] == 60
        assert call_args[1]["context"]["ip_address"] == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_send_password_reset_confirmation_email(self, email_service, mock_user, mock_smtp):
        """Test sending password reset confirmation email."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)
        email_service.send_template_email = AsyncMock(return_value=True)

        result = await email_service.send_password_reset_confirmation_email(mock_user)

        assert result is True
        email_service.send_template_email.assert_called_once()
        call_args = email_service.send_template_email.call_args
        assert call_args[1]["template_name"] == "password_reset_confirmation"
        assert "has been reset" in call_args[1]["subject"]

    @pytest.mark.asyncio
    async def test_send_team_invitation_email(self, email_service, mock_smtp):
        """Test sending team invitation email."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)
        email_service.send_template_email = AsyncMock(return_value=True)

        result = await email_service.send_team_invitation_email(
            invitee_email="invitee@test.com",
            inviter_name="John Doe",
            team_name="Test Team",
            invitation_url="https://app.test.com/invite/abc123",
        )

        assert result is True
        email_service.send_template_email.assert_called_once()
        call_args = email_service.send_template_email.call_args
        assert call_args[1]["template_name"] == "team_invitation"
        assert call_args[1]["to_email"] == "invitee@test.com"
        assert "John Doe invited you" in call_args[1]["subject"]

    @pytest.mark.asyncio
    async def test_send_team_invitation_email_fallback(self, email_service, mock_smtp):
        """Test sending team invitation email with fallback."""
        email_service._create_smtp_connection = Mock(return_value=mock_smtp)

        # Mock template sending failure to trigger fallback
        email_service.send_template_email = AsyncMock(side_effect=Exception("Template error"))

        result = await email_service.send_team_invitation_email(
            invitee_email="invitee@test.com",
            inviter_name="John Doe",
            team_name="Test Team",
            invitation_url="https://app.test.com/invite/abc123",
        )

        assert result is True
        mock_smtp.send_message.assert_called_once()


class TestAsyncToSyncDecorator:
    """Test the async_to_sync decorator."""

    def test_async_to_sync_decorator(self):
        """Test that async functions can be called synchronously."""
        from app.lib.email import async_to_sync

        @async_to_sync
        async def async_function(value):
            return f"Result: {value}"

        result = async_function("test")
        assert result == "Result: test"
