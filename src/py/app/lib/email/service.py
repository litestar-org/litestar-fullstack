"""Application-specific email service with template rendering for ``litestar-email`` 0.4.0."""

from __future__ import annotations

import html as html_lib
import re
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

import structlog
from litestar_email import EmailMultiAlternatives, EmailService
from litestar_email.exceptions import (
    EmailAuthenticationError,
    EmailConnectionError,
    EmailDeliveryError,
    EmailRateLimitError,
)

from app.lib.settings import BASE_DIR, get_settings

logger = structlog.get_logger(__name__)

HTML_TAG_PATTERN = re.compile(r"<[^<]+?>")
_URL_KEYS = frozenset({"VERIFICATION_URL", "RESET_URL", "LOGIN_URL", "INVITATION_URL"})
_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


class UserProtocol(Protocol):
    """Protocol for User objects used in email methods."""

    @property
    def email(self) -> str:
        """User email address."""
        ...

    @property
    def name(self) -> str | None:
        """Optional display name."""
        ...


class AppEmailService:
    """Template-rendering transactional email adapter over ``litestar-email`` ``EmailService``."""

    __slots__ = ("_mailer", "_settings", "_template_cache", "_template_dir")

    def __init__(self, mailer: EmailService) -> None:
        """Initialize the email service with a request- or task-scoped ``EmailService``."""
        self._mailer = mailer
        self._settings = get_settings()
        self._template_dir = Path(BASE_DIR / "server" / "static" / "email")
        self._template_cache: dict[str, str] = {}

    @property
    def app_name(self) -> str:
        """Configured application display name."""
        return self._settings.app.NAME

    @property
    def base_url(self) -> str:
        """Configured application base URL."""
        return self._settings.app.URL

    def _resolve_user_details(self, user: UserProtocol) -> tuple[str, str]:
        return user.email, user.name or "there"

    def _load_template(self, template_name: str) -> str:
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        template_path = self._template_dir / template_name
        rendered = template_path.read_text(encoding="utf-8")
        self._template_cache[template_name] = rendered
        return rendered

    def _render_template(self, template_name: str, context: dict[str, str | int]) -> str:
        content = self._load_template(template_name)
        merged = {"APP_NAME": self.app_name, **context}
        for key, value in merged.items():
            text_value = self._validate_http_url(str(value)) if key in _URL_KEYS else str(value)
            substituted = html_lib.escape(text_value, quote=True)
            content = content.replace(f"{{{{{key}}}}}", substituted)
        return content

    async def send_email(
        self,
        to_email: str | list[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
        from_email: str | None = None,
        reply_to: str | None = None,
        *,
        template_name: str | None = None,
    ) -> bool:
        """Send an HTML + plain-text multipart email and log structured delivery failures.

        Returns:
            ``True`` if at least one message was accepted by the email backend.

        Raises:
            EmailRateLimitError: If the email backend rejects the request due to rate limiting.
            EmailAuthenticationError: If backend authentication fails.
            EmailConnectionError: If the backend connection fails.
            EmailDeliveryError: If the backend reports a delivery failure.
        """
        if not text_content:
            text_content = self._html_to_text(html_content)

        recipients = [to_email] if isinstance(to_email, str) else list(to_email)
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
        except EmailRateLimitError as exc:
            await logger.awarning(
                "Email delivery rate limited",
                recipient_count=len(recipients),
                template=template_name,
                error_type=type(exc).__name__,
            )
            raise
        except EmailAuthenticationError as exc:
            await logger.aerror(
                "Email backend authentication failed",
                recipient_count=len(recipients),
                template=template_name,
                error_type=type(exc).__name__,
            )
            raise
        except EmailConnectionError as exc:
            await logger.awarning(
                "Email backend connection failed",
                recipient_count=len(recipients),
                template=template_name,
                error_type=type(exc).__name__,
            )
            raise
        except EmailDeliveryError as exc:
            await logger.aerror(
                "Email delivery failed",
                recipient_count=len(recipients),
                template=template_name,
                error_type=type(exc).__name__,
            )
            raise
        else:
            return num_sent > 0

    async def send_verification_email(self, user: UserProtocol, verification_token: str) -> bool:
        """Send an account email verification message.

        Returns:
            ``True`` if the message was sent.
        """
        verification_url = f"{self.base_url.rstrip('/')}/verify-email?token={verification_token}"
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
            template_name="email-verification.html",
        )

    async def send_welcome_email(self, user: UserProtocol) -> bool:
        """Send a welcome message to a newly verified user.

        Returns:
            ``True`` if the message was sent.
        """
        login_url = f"{self.base_url.rstrip('/')}/login"
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
            template_name="welcome.html",
        )

    async def send_password_reset_email(
        self,
        user: UserProtocol,
        reset_token: str,
        expires_in_minutes: int = 60,
    ) -> bool:
        """Send a password reset message.

        Returns:
            ``True`` if the message was sent.
        """
        reset_url = f"{self.base_url.rstrip('/')}/reset-password?token={reset_token}"
        user_email, user_name = self._resolve_user_details(user)
        expires_hours = max(1, (expires_in_minutes + 59) // 60)
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
            template_name="password-reset.html",
        )

    async def send_password_reset_confirmation_email(self, user: UserProtocol) -> bool:
        """Send a password reset confirmation message.

        Returns:
            ``True`` if the message was sent.
        """
        login_url = f"{self.base_url.rstrip('/')}/login"
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
            template_name="password-reset-confirmation.html",
        )

    async def send_team_invitation_email(
        self,
        invitee_email: str,
        inviter_name: str,
        team_name: str,
        invitation_url: str,
    ) -> bool:
        """Send a team invitation message.

        Returns:
            ``True`` if the message was sent.
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
            template_name="team-invitation.html",
        )

    @staticmethod
    def _validate_http_url(url: str) -> str:
        stripped = url.strip()
        parsed = urlsplit(stripped)
        if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES or not parsed.netloc:
            msg = "Template URL must use http or https scheme with a valid host"
            raise ValueError(msg)
        return stripped

    def _html_to_text(self, html_content: str) -> str:
        text = HTML_TAG_PATTERN.sub("", html_content)
        text = html_lib.unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
