"""Email module for transactional email delivery.

This module provides a complete email system with:
- Pluggable backend support (SMTP, Console, InMemory)
- High-level service for transactional emails

Example:
    from app.lib.email import EmailService, get_backend

    # Send a simple email
    service = EmailService()
    await service.send_verification_email(user, token)

    # Use backend directly for bulk sending
    async with get_backend() as backend:
        await backend.send_messages([msg1, msg2, msg3])
"""

from __future__ import annotations

from app.lib.email.backends import get_backend, get_backend_class, list_backends, register_backend
from app.lib.email.backends.base import BaseEmailBackend
from app.lib.email.base import EmailMessage, EmailMultiAlternatives
from app.lib.email.service import EmailService, email_service

__all__ = [
    "BaseEmailBackend",
    "EmailMessage",
    "EmailMultiAlternatives",
    "EmailService",
    "email_service",
    "get_backend",
    "get_backend_class",
    "list_backends",
    "register_backend",
]
