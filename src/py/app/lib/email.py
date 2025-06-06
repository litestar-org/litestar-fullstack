"""Email service for sending verification emails."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from litestar.contrib.jinja import JinjaTemplateEngine

if TYPE_CHECKING:
    from app.db.models import EmailVerificationToken, PasswordResetToken, User

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self, base_url: str = "http://localhost:8000", app_name: str = "Litestar App") -> None:
        """Initialize email service.

        Args:
            base_url: Base URL for the application (used for verification links)
            app_name: Name of the application for email branding
        """
        self.base_url = base_url
        self.app_name = app_name
        # Initialize template engine for email templates
        from app.lib.settings import get_settings
        settings = get_settings()
        self.template_dir = settings.vite.TEMPLATE_DIR
        self.template_engine = JinjaTemplateEngine(directory=self.template_dir)

    async def send_verification_email(
        self,
        user: User,
        verification_token: EmailVerificationToken
    ) -> None:
        """Send email verification email to user.

        Args:
            user: The user to send the email to
            verification_token: The verification token
        """
        verification_url = f"{self.base_url}/verify-email?token={verification_token.token}"

        # TODO: Implement actual email sending
        # For now, just log the email content
        logger.info(
            "Email verification sent to %s. Verification URL: %s",
            user.email,
            verification_url
        )

        # In a real implementation, this would send an email using
        # a service like SendGrid, AWS SES, or SMTP
        # Example email content:
        email_content = f"""
        Hi {user.name or 'there'},

        Please verify your email address by clicking the link below:
        {verification_url}

        This link will expire in 24 hours.

        If you didn't create an account, please ignore this email.

        Best regards,
        Your App Team
        """

        logger.info("Email content would be: %s", email_content)

    async def send_welcome_email(self, user: User) -> None:
        """Send welcome email to newly verified user.

        Args:
            user: The user to send the welcome email to
        """
        # TODO: Implement actual welcome email sending
        logger.info("Welcome email would be sent to %s", user.email)

    async def send_password_reset_email(
        self,
        user: User,
        reset_token: PasswordResetToken,
        expires_in_minutes: int = 60,
        ip_address: str = "unknown"
    ) -> None:
        """Send password reset email to user.

        Args:
            user: The user to send the email to
            reset_token: The password reset token
            expires_in_minutes: How long the token is valid for
            ip_address: IP address where reset was requested
        """
        reset_url = f"{self.base_url}/reset-password?token={reset_token.token}"

        # Render HTML template
        from jinja2 import Template
        html_template = Path(f"{self.template_dir}/emails/password_reset.html.j2").read_text()
        template = Template(html_template)
        html_content = template.render(
            app_name=self.app_name,
            user=user,
            reset_url=reset_url,
            expires_in_minutes=expires_in_minutes,
            ip_address=ip_address,
        )

        # Render text template
        text_template = Path(f"{self.template_dir}/emails/password_reset.txt.j2").read_text()
        template = Template(text_template)
        text_content = template.render(
            app_name=self.app_name,
            user=user,
            reset_url=reset_url,
            expires_in_minutes=expires_in_minutes,
            ip_address=ip_address,
        )

        # TODO: Implement actual email sending
        # For now, just log the email content
        logger.info(
            "Password reset email sent to %s. Reset URL: %s",
            user.email,
            reset_url
        )
        logger.debug("HTML content: %s", html_content)
        logger.debug("Text content: %s", text_content)

        # In a real implementation, this would send an email using
        # a service like SendGrid, AWS SES, or SMTP with both HTML and text content

    async def send_password_reset_confirmation_email(
        self,
        user: User,
        reset_time: datetime | None = None
    ) -> None:
        """Send password reset confirmation email to user.

        Args:
            user: The user whose password was reset
            reset_time: When the password was reset (defaults to now)
        """
        if reset_time is None:
            reset_time = datetime.now(UTC)

        login_url = f"{self.base_url}/login"

        # Render HTML template
        from jinja2 import Template
        html_template = Path(f"{self.template_dir}/emails/password_reset_confirmation.html.j2").read_text()
        template = Template(html_template)
        html_content = template.render(
            app_name=self.app_name,
            user=user,
            login_url=login_url,
            reset_time=reset_time.strftime("%B %d, %Y at %I:%M %p UTC"),
        )

        # Render text template
        text_template = Path(f"{self.template_dir}/emails/password_reset_confirmation.txt.j2").read_text()
        template = Template(text_template)
        text_content = template.render(
            app_name=self.app_name,
            user=user,
            login_url=login_url,
            reset_time=reset_time.strftime("%B %d, %Y at %I:%M %p UTC"),
        )

        # TODO: Implement actual email sending
        # For now, just log the email content
        logger.info(
            "Password reset confirmation email sent to %s",
            user.email
        )
        logger.debug("HTML content: %s", html_content)
        logger.debug("Text content: %s", text_content)

        # In a real implementation, this would send an email using
        # a service like SendGrid, AWS SES, or SMTP with both HTML and text content


# Global email service instance
email_service = EmailService()
