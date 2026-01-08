"""Application-specific email service with template rendering.

This module provides the AppEmailService class which wraps the litestar-email
plugin's EmailService to provide template-aware transactional email methods.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from litestar_email import EmailMultiAlternatives

from app.lib.settings import BASE_DIR, get_settings

if TYPE_CHECKING:
    from litestar_email import EmailService

logger = logging.getLogger(__name__)

HTML_TAG_PATTERN = re.compile(r"<[^<]+?>")


class UserProtocol(Protocol):
    """Protocol for User objects used in email methods."""

    email: str
    name: str | None


class AppEmailService:
    """High-level service for sending transactional emails with templates.

    This wraps the litestar-email plugin's EmailService to provide
    template rendering and app-specific email methods.

    The service is injected via Litestar's DI system and receives
    the plugin's EmailService (mailer) for actual email sending.

    Example:
        # In a controller, inject via DI:
        async def signup(app_email_service: AppEmailService, ...):
            await app_email_service.send_verification_email(user, token)
    """

    __slots__ = ("_mailer", "_settings", "_template_cache", "_template_dir")

    def __init__(self, mailer: EmailService) -> None:
        """Initialize the email service.

        Args:
            mailer: The litestar-email plugin's EmailService instance.
        """
        self._mailer = mailer
        self._settings = get_settings()
        self._template_dir = Path(BASE_DIR / "server" / "static" / "email")
        self._template_cache: dict[str, str] = {}

    @property
    def app_name(self) -> str:
        """Get application name from settings."""
        return self._settings.app.NAME

    @property
    def base_url(self) -> str:
        """Get base URL from settings."""
        return self._settings.app.URL

    def _resolve_user_details(self, user: UserProtocol) -> tuple[str, str]:
        """Normalize user details for templating and delivery."""
        user_name = user.name or "there"
        return user.email, user_name

    def _load_template(self, template_name: str) -> str:
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        template_path = self._template_dir / template_name
        html = template_path.read_text(encoding="utf-8")
        self._template_cache[template_name] = html
        return html

    def _render_template(self, template_name: str, context: dict[str, str | int]) -> str:
        html = self._load_template(template_name)
        context = {"APP_NAME": self.app_name, **context}
        for key, value in context.items():
            html = html.replace(f"{{{{{key}}}}}", str(value))
        return html

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
        if not text_content:
            text_content = self._html_to_text(html_content)

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
            num_sent = await self._mailer.send_message(message)
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            raise
        else:
            return num_sent > 0

    async def send_verification_email(self, user: UserProtocol, verification_token: str) -> bool:
        """Send email verification email to user.

        Args:
            user: The user to send the email to.
            verification_token: The verification token string.

        Returns:
            True if email was sent successfully.
        """
        verification_url = f"{self.base_url}/verify-email?token={verification_token}"
        user_email, user_name = self._resolve_user_details(user)

        html_content = self._render_template(
            "email-verification.html",
            {
                "USER_NAME": user_name,
                "VERIFICATION_URL": verification_url,
                "EXPIRES_HOURS": 24,
            },
        )

        return await self.send_email(
            to_email=user_email,
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
        user_email, user_name = self._resolve_user_details(user)

        html_content = self._render_template(
            "welcome.html",
            {
                "USER_NAME": user_name,
                "LOGIN_URL": login_url,
            },
        )

        return await self.send_email(
            to_email=user_email,
            subject=f"Welcome to {self.app_name}!",
            html_content=html_content,
        )

    async def send_password_reset_email(
        self,
        user: UserProtocol,
        reset_token: str,
        expires_in_minutes: int = 60,
    ) -> bool:
        """Send password reset email to user.

        Args:
            user: The user to send the email to.
            reset_token: The password reset token string.
            expires_in_minutes: How long the token is valid for.

        Returns:
            True if email was sent successfully.
        """
        reset_url = f"{self.base_url}/reset-password?token={reset_token}"
        user_email, user_name = self._resolve_user_details(user)

        expires_hours = max(1, int((expires_in_minutes + 59) // 60))
        html_content = self._render_template(
            "password-reset.html",
            {
                "USER_NAME": user_name,
                "RESET_URL": reset_url,
                "EXPIRES_HOURS": expires_hours,
            },
        )

        return await self.send_email(
            to_email=user_email,
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
        user_email, user_name = self._resolve_user_details(user)

        html_content = self._render_template(
            "password-reset-confirmation.html",
            {
                "USER_NAME": user_name,
                "LOGIN_URL": login_url,
            },
        )

        return await self.send_email(
            to_email=user_email,
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
        html_content = self._render_template(
            "team-invitation.html",
            {
                "INVITER_NAME": inviter_name,
                "TEAM_NAME": team_name,
                "INVITATION_URL": invitation_url,
            },
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
        text = re.sub(r"\s+", " ", text)
        return text.strip()
