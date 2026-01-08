"""Email module - wraps litestar-email plugin with app-specific functionality.

This module re-exports the litestar-email plugin's classes and adds the
AppEmailService for template-based transactional emails.

Example:
    # In a controller, inject via DI:
    async def signup(app_email_service: AppEmailService, ...):
        await app_email_service.send_verification_email(user, token)

    # Or use the plugin's EmailService directly for simpler emails:
    async def send_notification(mailer: EmailService, ...):
        await mailer.send_message(EmailMessage(...))
"""

from __future__ import annotations

from litestar_email import (
    EmailConfig,
    EmailMessage,
    EmailMultiAlternatives,
    EmailPlugin,
    EmailService,
    InMemoryBackend,
)

from app.lib.email.service import AppEmailService, UserProtocol

__all__ = [
    "AppEmailService",
    "EmailConfig",
    "EmailMessage",
    "EmailMultiAlternatives",
    "EmailPlugin",
    "EmailService",
    "InMemoryBackend",
    "UserProtocol",
]
