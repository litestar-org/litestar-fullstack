"""Transactional email dispatch tasks backed by ``litestar-queues`` and ``AppEmailService``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from litestar_queues import RetryBackoff, get_current_task_context, task

from app.lib.email import AppEmailService

__all__ = (
    "send_password_reset_confirmation_email_task",
    "send_password_reset_email_task",
    "send_team_invitation_email_task",
    "send_verification_email_task",
    "send_welcome_email_task",
)

_EMAIL_RETRY = RetryBackoff(initial_delay=2.0, multiplier=2.0, max_delay=120.0)


@dataclass(frozen=True, slots=True)
class _EmailRecipient:
    email: str
    name: str | None = None


def _minutes_until(expires_at: str | None, default: int = 60) -> int:
    if not expires_at:
        return default
    try:
        parsed = datetime.fromisoformat(expires_at)
    except ValueError:
        return default
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    remaining = int((parsed - datetime.now(UTC)).total_seconds() // 60)
    return max(1, remaining)


@task(
    "email.send_verification",
    queue="emails",
    retries=3,
    retry_backoff=_EMAIL_RETRY,
    unique_by="arguments",
)
async def send_verification_email_task(
    email: str,
    token: str,
    token_expires_at: str | None = None,
    return_url: str | None = None,
    user_name: str | None = None,
) -> bool:
    """Deliver an account email-verification message.

    Returns:
        ``True`` if the email was accepted for delivery, otherwise ``False``.
    """
    from app import config

    _ = (token_expires_at, return_url)
    context = get_current_task_context()
    if context is not None:
        await context.log("Sending verification email")
    async with config.email.provide_service() as mailer:
        service = AppEmailService(mailer=mailer)
        return await service.send_verification_email(_EmailRecipient(email=email, name=user_name), token)


@task(
    "email.send_password_reset",
    queue="emails",
    retries=3,
    retry_backoff=_EMAIL_RETRY,
    unique_by="arguments",
)
async def send_password_reset_email_task(
    email: str,
    token: str,
    token_expires_at: str | None = None,
    return_url: str | None = None,
    user_name: str | None = None,
) -> bool:
    """Deliver a password-reset message.

    Returns:
        ``True`` if the email was accepted for delivery, otherwise ``False``.
    """
    from app import config

    _ = return_url
    context = get_current_task_context()
    if context is not None:
        await context.log("Sending password reset email")
    expires_in_minutes = _minutes_until(token_expires_at, default=60)
    async with config.email.provide_service() as mailer:
        service = AppEmailService(mailer=mailer)
        return await service.send_password_reset_email(
            _EmailRecipient(email=email, name=user_name),
            token,
            expires_in_minutes=expires_in_minutes,
        )


@task(
    "email.send_password_reset_confirmation",
    queue="emails",
    retries=3,
    retry_backoff=_EMAIL_RETRY,
    unique_by="arguments",
)
async def send_password_reset_confirmation_email_task(
    email: str,
    token: str | None = None,
    token_expires_at: str | None = None,
    return_url: str | None = None,
    user_name: str | None = None,
) -> bool:
    """Deliver a password-reset confirmation message.

    Returns:
        ``True`` if the email was accepted for delivery, otherwise ``False``.
    """
    from app import config

    _ = (token, token_expires_at, return_url)
    context = get_current_task_context()
    if context is not None:
        await context.log("Sending password reset confirmation email")
    async with config.email.provide_service() as mailer:
        service = AppEmailService(mailer=mailer)
        return await service.send_password_reset_confirmation_email(_EmailRecipient(email=email, name=user_name))


@task(
    "email.send_welcome",
    queue="emails",
    retries=3,
    retry_backoff=_EMAIL_RETRY,
    unique_by="arguments",
)
async def send_welcome_email_task(
    email: str,
    user_name: str | None = None,
) -> bool:
    """Deliver a welcome message to a newly verified user.

    Returns:
        ``True`` if the email was accepted for delivery, otherwise ``False``.
    """
    from app import config

    context = get_current_task_context()
    if context is not None:
        await context.log("Sending welcome email")
    async with config.email.provide_service() as mailer:
        service = AppEmailService(mailer=mailer)
        return await service.send_welcome_email(_EmailRecipient(email=email, name=user_name))


@task(
    "email.send_team_invitation",
    queue="emails",
    retries=3,
    retry_backoff=_EMAIL_RETRY,
    unique_by="arguments",
)
async def send_team_invitation_email_task(
    invitee_email: str,
    inviter_name: str,
    team_name: str,
    invitation_url: str,
) -> bool:
    """Deliver a team invitation email.

    Returns:
        ``True`` if the email was accepted for delivery, otherwise ``False``.
    """
    from app import config

    context = get_current_task_context()
    if context is not None:
        await context.log("Sending team invitation email")
    async with config.email.provide_service() as mailer:
        service = AppEmailService(mailer=mailer)
        return await service.send_team_invitation_email(
            invitee_email=invitee_email,
            inviter_name=inviter_name,
            team_name=team_name,
            invitation_url=invitation_url,
        )
