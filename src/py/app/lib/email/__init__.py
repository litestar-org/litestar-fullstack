"""Email module wrapping ``litestar-email`` with template-backed ``AppEmailService``."""

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
