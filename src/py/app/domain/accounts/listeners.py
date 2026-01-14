"""Account domain signals/events."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import structlog
from litestar.events import listener

from app.domain.accounts import deps
from app.lib.deps import provide_services

if TYPE_CHECKING:
    from uuid import UUID

    from app.lib.email import AppEmailService
    from app.lib.email.service import UserProtocol

logger = structlog.get_logger()


@listener("user_created")
async def user_created_event_handler(user_id: UUID, mailer: AppEmailService) -> None:
    """Executes when a new user is created.

    Args:
        user_id: The primary key of the user that was created.
        mailer: The application email service.
    """
    await logger.ainfo("Running post signup flow.")
    async with provide_services(deps.provide_users_service, deps.provide_email_verification_service) as (
        users_service,
        verification_service,
    ):
        user = await users_service.get_one_or_none(id=user_id)
        if user is None:
            await logger.aerror("Could not locate the specified user", id=user_id)
            return

        await logger.ainfo("Found user", **user.to_dict(exclude={"hashed_password"}))

        if not user.is_verified:
            _, verification_token = await verification_service.create_verification_token(
                user_id=user.id, email=user.email
            )
            await mailer.send_verification_email(cast("UserProtocol", user), verification_token)

            await logger.ainfo("Sent verification email for user", user_id=user.id)


@listener("password_reset_requested")
async def password_reset_requested_event_handler(user_id: UUID, mailer: AppEmailService) -> None:
    """Executes when a password reset is requested.

    Args:
        user_id: The primary key of the user that requested the reset.
        mailer: The application email service.
    """
    await logger.ainfo("Running password reset request flow.")
    async with provide_services(deps.provide_users_service, deps.provide_password_reset_service) as (
        users_service,
        password_reset_service,
    ):
        user = await users_service.get_one_or_none(id=user_id)
        if user is None:
            await logger.aerror("Could not locate the specified user", id=user_id)
            return

        _, reset_token = await password_reset_service.create_reset_token(user_id=user.id)

        await mailer.send_password_reset_email(
            user=cast("UserProtocol", user),
            reset_token=reset_token,
            expires_in_minutes=60,
        )
        await logger.ainfo("Sent password reset email for user", user_id=user.id)


@listener("password_reset_completed")
async def password_reset_completed_event_handler(user_id: UUID, mailer: AppEmailService) -> None:
    """Executes when a password reset is completed.

    Args:
        user_id: The primary key of the user that resets the password.
        mailer: The application email service.
    """
    await logger.ainfo("Running password reset completion flow.")
    async with provide_services(deps.provide_users_service) as (users_service,):
        user = await users_service.get_one_or_none(id=user_id)
        if user is None:
            await logger.aerror("Could not locate the specified user", id=user_id)
            return

        await mailer.send_password_reset_confirmation_email(cast("UserProtocol", user))
        await logger.ainfo("Sent password reset confirmation email for user", user_id=user.id)


@listener("verification_requested")
async def verification_requested_event_handler(user_id: UUID, mailer: AppEmailService) -> None:
    """Executes when a manual verification is requested.

    Args:
        user_id: The primary key of the user.
        mailer: The application email service.
    """
    await logger.ainfo("Running verification request flow.")
    async with provide_services(deps.provide_users_service, deps.provide_email_verification_service) as (
        users_service,
        verification_service,
    ):
        user = await users_service.get_one_or_none(id=user_id)
        if user is None:
            await logger.aerror("Could not locate the specified user", id=user_id)
            return

        if user.is_verified:
            await logger.ainfo("User already verified, skipping email", user_id=user.id)
            return

        _, verification_token = await verification_service.create_verification_token(user_id=user.id, email=user.email)
        await mailer.send_verification_email(cast("UserProtocol", user), verification_token)
        await logger.ainfo("Sent verification email for user", user_id=user.id)


__all__ = (
    "password_reset_completed_event_handler",
    "password_reset_requested_event_handler",
    "user_created_event_handler",
    "verification_requested_event_handler",
)
