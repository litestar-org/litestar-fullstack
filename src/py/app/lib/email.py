"""Email service for sending transactional emails using SMTP."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import smtplib
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from functools import wraps
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.lib.settings import get_settings

if TYPE_CHECKING:
    from app.db.models import EmailVerificationToken, PasswordResetToken, User

logger = logging.getLogger(__name__)


def async_to_sync(func: Any) -> Any:
    """Decorator to run async functions in sync context."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self) -> None:
        """Initialize email service with settings."""
        settings = get_settings()
        self.settings = settings.email
        self.app_settings = settings.app
        self.base_url = settings.app.URL
        self.app_name = settings.app.NAME

        # Initialize Jinja2 template environment
        self.template_dir = settings.vite.TEMPLATE_DIR
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir), autoescape=select_autoescape(["html", "xml"])
        )

    def _create_smtp_connection(self) -> smtplib.SMTP | smtplib.SMTP_SSL | None:
        """Create SMTP connection based on settings.

        Returns:
            SMTP connection or None if email is disabled
        """
        if not self.settings.ENABLED:
            logger.warning("Email service is disabled. Enable with EMAIL_ENABLED=true")
            return None

        try:
            # Use SSL connection if specified
            if self.settings.USE_SSL:
                smtp = smtplib.SMTP_SSL(self.settings.SMTP_HOST, self.settings.SMTP_PORT, timeout=self.settings.TIMEOUT)
            else:
                smtp = smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT, timeout=self.settings.TIMEOUT)

            # Start TLS if specified (and not already using SSL)
            if self.settings.USE_TLS and not self.settings.USE_SSL:
                smtp.starttls()

            # Login if credentials provided
            if self.settings.SMTP_USER and self.settings.SMTP_PASSWORD:
                smtp.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)

        except Exception:
            logger.exception("Failed to create SMTP connection")
            return None

        return smtp

    async def send_email(
        self,
        to_email: str | list[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
    ) -> bool:
        """Send email with HTML and optional text content.

        Args:
            to_email: Recipient email address(es)
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text content (optional, generated from HTML if not provided)
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            reply_to: Reply-to email address (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        # Check if email is enabled
        if not self.settings.ENABLED:
            logger.info("Email service disabled. Would send email to %s with subject: %s", to_email, subject)
            logger.debug("HTML content: %s", html_content[:200] + "...")
            return False

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((from_name or self.settings.FROM_NAME, from_email or self.settings.FROM_EMAIL))

        # Handle multiple recipients
        if isinstance(to_email, list):
            msg["To"] = ", ".join(to_email)
        else:
            msg["To"] = to_email

        if reply_to:
            msg["Reply-To"] = reply_to

        # Add text content (required for spam filters)
        if not text_content:
            # Simple HTML to text conversion
            import re

            text_content = re.sub("<[^<]+?>", "", html_content)
            text_content = text_content.replace("&nbsp;", " ").strip()

        text_part = MIMEText(text_content, "plain")
        msg.attach(text_part)

        # Add HTML content
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # Send email
        smtp = None
        try:
            smtp = self._create_smtp_connection()
            if not smtp:
                return False

            # Send to multiple recipients if needed
            recipients = to_email if isinstance(to_email, list) else [to_email]
            smtp.send_message(msg, to_addrs=recipients)

            logger.info("Email sent successfully to %s with subject: %s", to_email, subject)
            return True

        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            return False

        finally:
            if smtp:
                with contextlib.suppress(Exception):
                    smtp.quit()

    async def send_template_email(
        self,
        template_name: str,
        to_email: str | list[str],
        subject: str,
        context: dict[str, Any],
        from_email: str | None = None,
        from_name: str | None = None,
    ) -> bool:
        """Send email using a template.

        Args:
            template_name: Name of template file (without extension)
            to_email: Recipient email address(es)
            subject: Email subject
            context: Template context variables
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Load templates
            html_template = self.jinja_env.get_template(f"emails/{template_name}.html.j2")

            # Try to load text template, fall back to HTML stripping
            text_content = None
            try:
                text_template = self.jinja_env.get_template(f"emails/{template_name}.txt.j2")
                text_content = text_template.render(**context)
            except Exception:
                logger.debug("Text template not found for %s", template_name)

            # Render HTML content
            html_content = html_template.render(**context)

            # Send email
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email,
                from_name=from_name,
            )

        except Exception:
            logger.exception("Failed to send template email %s", template_name)
            return False

    async def send_verification_email(self, user: User, verification_token: EmailVerificationToken) -> bool:
        """Send email verification email to user.

        Args:
            user: The user to send the email to
            verification_token: The verification token

        Returns:
            True if email was sent successfully
        """
        verification_url = f"{self.base_url}/verify-email?token={verification_token.token}"

        context = {
            "app_name": self.app_name,
            "user": user,
            "verification_url": verification_url,
            "expires_in_hours": 24,
        }

        # Try template first, fall back to simple email
        try:
            return await self.send_template_email(
                template_name="email_verification",
                to_email=user.email,
                subject=f"Verify your email address for {self.app_name}",
                context=context,
            )
        except Exception:
            # Fallback to simple email
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to {self.app_name}!</h2>
                <p>Hi {user.name or "there"},</p>
                <p>Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
                <p>Or copy and paste this URL into your browser:</p>
                <p>{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create an account, please ignore this email.</p>
                <p>Best regards,<br>{self.app_name} Team</p>
            </body>
            </html>
            """

            return await self.send_email(
                to_email=user.email,
                subject=f"Verify your email address for {self.app_name}",
                html_content=html_content,
            )

    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to newly verified user.

        Args:
            user: The user to send the welcome email to

        Returns:
            True if email was sent successfully
        """
        context = {
            "app_name": self.app_name,
            "user": user,
            "login_url": f"{self.base_url}/login",
        }

        try:
            return await self.send_template_email(
                template_name="welcome",
                to_email=user.email,
                subject=f"Welcome to {self.app_name}!",
                context=context,
            )
        except Exception:
            # Fallback to simple email
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to {self.app_name}!</h2>
                <p>Hi {user.name or "there"},</p>
                <p>Your email has been verified and your account is now active.</p>
                <p>You can now log in and start using {self.app_name}.</p>
                <p><a href="{context["login_url"]}" style="display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">Log In Now</a></p>
                <p>If you have any questions, feel free to reach out to our support team.</p>
                <p>Best regards,<br>{self.app_name} Team</p>
            </body>
            </html>
            """

            return await self.send_email(
                to_email=user.email,
                subject=f"Welcome to {self.app_name}!",
                html_content=html_content,
            )

    async def send_password_reset_email(
        self, user: User, reset_token: PasswordResetToken, expires_in_minutes: int = 60, ip_address: str = "unknown"
    ) -> bool:
        """Send password reset email to user.

        Args:
            user: The user to send the email to
            reset_token: The password reset token
            expires_in_minutes: How long the token is valid for
            ip_address: IP address where reset was requested

        Returns:
            True if email was sent successfully
        """
        reset_url = f"{self.base_url}/reset-password?token={reset_token.token}"

        context = {
            "app_name": self.app_name,
            "user": user,
            "reset_url": reset_url,
            "expires_in_minutes": expires_in_minutes,
            "ip_address": ip_address,
        }

        # Use existing templates
        return await self.send_template_email(
            template_name="password_reset",
            to_email=user.email,
            subject=f"Reset your password for {self.app_name}",
            context=context,
        )

    async def send_password_reset_confirmation_email(self, user: User, reset_time: datetime | None = None) -> bool:
        """Send password reset confirmation email to user.

        Args:
            user: The user whose password was reset
            reset_time: When the password was reset (defaults to now)

        Returns:
            True if email was sent successfully
        """
        if reset_time is None:
            reset_time = datetime.now(UTC)

        context = {
            "app_name": self.app_name,
            "user": user,
            "login_url": f"{self.base_url}/login",
            "reset_time": reset_time.strftime("%B %d, %Y at %I:%M %p UTC"),
        }

        # Use existing templates
        return await self.send_template_email(
            template_name="password_reset_confirmation",
            to_email=user.email,
            subject=f"Your password has been reset for {self.app_name}",
            context=context,
        )

    async def send_team_invitation_email(
        self, invitee_email: str, inviter_name: str, team_name: str, invitation_url: str
    ) -> bool:
        """Send team invitation email.

        Args:
            invitee_email: Email address to send invitation to
            inviter_name: Name of person sending invitation
            team_name: Name of the team
            invitation_url: URL to accept the invitation

        Returns:
            True if email was sent successfully
        """
        context = {
            "app_name": self.app_name,
            "inviter_name": inviter_name,
            "team_name": team_name,
            "invitation_url": invitation_url,
        }

        try:
            return await self.send_template_email(
                template_name="team_invitation",
                to_email=invitee_email,
                subject=f"{inviter_name} invited you to join {team_name} on {self.app_name}",
                context=context,
            )
        except Exception:
            # Fallback to simple email
            html_content = f"""
            <html>
            <body>
                <h2>You're invited to join {team_name}!</h2>
                <p>{inviter_name} has invited you to join their team on {self.app_name}.</p>
                <p><a href="{invitation_url}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Accept Invitation</a></p>
                <p>Or copy and paste this URL into your browser:</p>
                <p>{invitation_url}</p>
                <p>If you don't want to join this team, you can safely ignore this email.</p>
                <p>Best regards,<br>{self.app_name} Team</p>
            </body>
            </html>
            """

            return await self.send_email(
                to_email=invitee_email,
                subject=f"{inviter_name} invited you to join {team_name} on {self.app_name}",
                html_content=html_content,
            )


# Global email service instance
email_service = EmailService()
