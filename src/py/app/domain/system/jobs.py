"""System domain background jobs."""

from __future__ import annotations

from saq.types import Context
from structlog import get_logger

from app.domain.accounts import deps as account_deps

__all__ = ("cleanup_auth_tokens",)

logger = get_logger()


async def cleanup_auth_tokens(_: Context) -> dict[str, int]:
    """Remove expired auth tokens and return cleanup totals."""
    from app.config import alchemy

    async with alchemy.get_session() as db_session:
        verification_service = await anext(account_deps.provide_email_verification_service(db_session))
        reset_service = await anext(account_deps.provide_password_reset_service(db_session))
        refresh_service = await anext(account_deps.provide_refresh_token_service(db_session))

        verification_count = await verification_service.cleanup_expired_tokens()
        reset_count = await reset_service.cleanup_expired_tokens()
        refresh_count = await refresh_service.cleanup_expired_tokens()

    result = {
        "email_verification": verification_count,
        "password_reset": reset_count,
        "refresh_tokens": refresh_count,
    }
    await logger.ainfo("Token cleanup complete", **result)
    return result
