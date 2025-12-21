"""High-level email service.

This module provides the EmailService class which offers a high-level
API for sending various types of transactional emails including
verification, password reset, welcome, and team invitation emails.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Protocol

from app.lib.email.backends import get_backend
from app.lib.email.base import EmailMultiAlternatives
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from app.db.models import EmailVerificationToken, PasswordResetToken

logger = logging.getLogger(__name__)

# Pattern for stripping HTML tags for plain text fallback
HTML_TAG_PATTERN = re.compile(r"<[^<]+?>")


class UserProtocol(Protocol):
    """Protocol for User objects used in email methods."""

    email: str
    name: str | None


class EmailService:
    """High-level service for sending transactional emails.

    This service provides methods for sending various types of emails
    including verification, password reset, welcome, and invitation emails.

    The service uses the configured email backend for flexible email delivery.

    Example:
        service = EmailService()
        await service.send_verification_email(user, token)
        await service.send_password_reset_email(user, token)
    """

    def __init__(self, fail_silently: bool = False) -> None:
        """Initialize the email service.

        Args:
            fail_silently: If True, suppress exceptions during send.
        """
        self.fail_silently = fail_silently
        self._settings = get_settings()

    @property
    def app_name(self) -> str:
        """Get application name from settings."""
        return self._settings.app.NAME

    @property
    def base_url(self) -> str:
        """Get base URL from settings."""
        return self._settings.app.URL

    async def send_email(
        self,
        to_email: str | list[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
        from_email: str | None = None,
        reply_to: str | None = None,
    ) -> bool:
        """Send an email with HTML and optional text content.

        Args:
            to_email: Recipient email address(es).
            subject: Email subject.
            html_content: HTML email content.
            text_content: Plain text content (generated from HTML if not provided).
            from_email: Sender email (uses default if not provided).
            reply_to: Reply-to email address.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        if not self._settings.email.ENABLED:
            logger.info("Email service disabled. Would send email to %s with subject: %s", to_email, subject)
            return False

        # Generate plain text from HTML if not provided
        if not text_content:
            text_content = self._html_to_text(html_content)

        # Normalize recipients to list
        recipients = [to_email] if isinstance(to_email, str) else to_email

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            html_body=html_content,
            from_email=from_email,
            to=recipients,
            reply_to=[reply_to] if reply_to else [],
        )

        try:
            backend = get_backend(fail_silently=self.fail_silently)
            num_sent = await backend.send_messages([message])
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            if not self.fail_silently:
                raise
            return False
        else:
            return num_sent > 0

    async def send_verification_email(self, user: UserProtocol, verification_token: EmailVerificationToken) -> bool:
        """Send email verification email to user.

        Args:
            user: The user to send the email to.
            verification_token: The verification token object.

        Returns:
            True if email was sent successfully.
        """
        verification_url = f"{self.base_url}/verify-email?token={verification_token.token}"

        html_content = self._generate_verification_html(
            user_name=user.name or "there",
            verification_url=verification_url,
        )

        return await self.send_email(
            to_email=user.email,
            subject=f"Verify your email address for {self.app_name}",
            html_content=html_content,
        )

    async def send_welcome_email(self, user: UserProtocol) -> bool:
        """Send welcome email to newly verified user.

        Args:
            user: The user to send the welcome email to.

        Returns:
            True if email was sent successfully.
        """
        login_url = f"{self.base_url}/login"

        html_content = self._generate_welcome_html(
            user_name=user.name or "there",
            login_url=login_url,
        )

        return await self.send_email(
            to_email=user.email,
            subject=f"Welcome to {self.app_name}!",
            html_content=html_content,
        )

    async def send_password_reset_email(
        self,
        user: UserProtocol,
        reset_token: PasswordResetToken,
        expires_in_minutes: int = 60,
        ip_address: str = "unknown",
    ) -> bool:
        """Send password reset email to user.

        Args:
            user: The user to send the email to.
            reset_token: The password reset token object.
            expires_in_minutes: How long the token is valid for.
            ip_address: IP address where reset was requested.

        Returns:
            True if email was sent successfully.
        """
        reset_url = f"{self.base_url}/reset-password?token={reset_token.token}"

        html_content = self._generate_password_reset_html(
            user_name=user.name or "there",
            reset_url=reset_url,
            expires_in_minutes=expires_in_minutes,
            ip_address=ip_address,
        )

        return await self.send_email(
            to_email=user.email,
            subject=f"Reset your password for {self.app_name}",
            html_content=html_content,
        )

    async def send_password_reset_confirmation_email(self, user: UserProtocol) -> bool:
        """Send password reset confirmation email to user.

        Args:
            user: The user whose password was reset.

        Returns:
            True if email was sent successfully.
        """
        login_url = f"{self.base_url}/login"

        html_content = self._generate_password_reset_confirmation_html(
            user_name=user.name or "there",
            login_url=login_url,
        )

        return await self.send_email(
            to_email=user.email,
            subject=f"Your password has been reset for {self.app_name}",
            html_content=html_content,
        )

    async def send_team_invitation_email(
        self,
        invitee_email: str,
        inviter_name: str,
        team_name: str,
        invitation_url: str,
    ) -> bool:
        """Send team invitation email.

        Args:
            invitee_email: Email address to send invitation to.
            inviter_name: Name of person sending invitation.
            team_name: Name of the team.
            invitation_url: URL to accept the invitation.

        Returns:
            True if email was sent successfully.
        """
        html_content = self._generate_team_invitation_html(
            inviter_name=inviter_name,
            team_name=team_name,
            invitation_url=invitation_url,
        )

        return await self.send_email(
            to_email=invitee_email,
            subject=f"{inviter_name} invited you to join {team_name} on {self.app_name}",
            html_content=html_content,
        )

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text.

        Args:
            html_content: HTML string to convert.

        Returns:
            Plain text string.
        """
        text = HTML_TAG_PATTERN.sub("", html_content)
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _generate_base_html(self, content: str) -> str:
        """Generate base HTML template.

        Args:
            content: Inner content for the email.

        Returns:
            Complete HTML email string.
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                     line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #1a73e8; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">{self.app_name}</h1>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0;">
                {content}
            </div>
            <div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
                <p>&copy; {self.app_name}</p>
            </div>
        </body>
        </html>
        """

    def _generate_verification_html(self, user_name: str, verification_url: str) -> str:
        """Generate verification email HTML."""
        content = f"""
            <p>Hi {user_name},</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}" style="display: inline-block; padding: 10px 20px;
                background-color: #1a73e8; color: white; text-decoration: none;
                border-radius: 4px;">Verify Email</a></p>
            <p>Or copy and paste this URL: {verification_url}</p>
            <p>This link expires in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        """
        return self._generate_base_html(content)

    def _generate_welcome_html(self, user_name: str, login_url: str) -> str:
        """Generate welcome email HTML."""
        content = f"""
            <p>Hi {user_name},</p>
            <p>Welcome to {self.app_name}! Your account is now active.</p>
            <p><a href="{login_url}" style="display: inline-block; padding: 10px 20px;
                background-color: #28a745; color: white; text-decoration: none;
                border-radius: 4px;">Log In</a></p>
        """
        return self._generate_base_html(content)

    def _generate_password_reset_html(
        self, user_name: str, reset_url: str, expires_in_minutes: int, ip_address: str
    ) -> str:
        """Generate password reset email HTML."""
        content = f"""
            <p>Hi {user_name},</p>
            <p>You requested to reset your password. Click the link below:</p>
            <p><a href="{reset_url}" style="display: inline-block; padding: 10px 20px;
                background-color: #1a73e8; color: white; text-decoration: none;
                border-radius: 4px;">Reset Password</a></p>
            <p>Or copy and paste this URL: {reset_url}</p>
            <p>This link expires in {expires_in_minutes} minutes.</p>
            <p>Requested from IP: {ip_address}</p>
            <p>If you didn't request this, please ignore this email.</p>
        """
        return self._generate_base_html(content)

    def _generate_password_reset_confirmation_html(self, user_name: str, login_url: str) -> str:
        """Generate password reset confirmation email HTML."""
        content = f"""
            <p>Hi {user_name},</p>
            <p>Your password has been successfully reset.</p>
            <p><a href="{login_url}" style="display: inline-block; padding: 10px 20px;
                background-color: #28a745; color: white; text-decoration: none;
                border-radius: 4px;">Log In</a></p>
            <p>If you didn't make this change, contact support immediately.</p>
        """
        return self._generate_base_html(content)

    def _generate_team_invitation_html(self, inviter_name: str, team_name: str, invitation_url: str) -> str:
        """Generate team invitation email HTML."""
        content = f"""
            <p>Hi there,</p>
            <p>{inviter_name} has invited you to join {team_name} on {self.app_name}.</p>
            <p><a href="{invitation_url}" style="display: inline-block; padding: 10px 20px;
                background-color: #1a73e8; color: white; text-decoration: none;
                border-radius: 4px;">Accept Invitation</a></p>
            <p>Or copy and paste this URL: {invitation_url}</p>
            <p>If you don't want to join this team, you can safely ignore this email.</p>
        """
        return self._generate_base_html(content)


# Global email service instance for backwards compatibility
email_service = EmailService()
