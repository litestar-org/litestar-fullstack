"""Re-confirmation of the caller's identity before sensitive account actions."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from litestar.exceptions import PermissionDeniedException, ServiceUnavailableException, TooManyRequestsException
from litestar_security import SecurityPlugin, VerificationUnavailable, requires_assurance
from litestar_security.accounts import PasswordReauthenticationProof, RateLimited
from litestar_security.accounts._operations import PASSWORD_VERIFY

if TYPE_CHECKING:
    from litestar import Request

    from app.db import models as m

__all__ = ("REAUTHENTICATION_REQUIRED", "RECENT_AUTHENTICATION_WINDOW", "confirm_authentication")

RECENT_AUTHENTICATION_WINDOW = timedelta(minutes=5)
REAUTHENTICATION_REQUIRED = "reauthentication_required"

_UNAVAILABLE = "Password verification is unavailable."
_recent_sign_in = requires_assurance(max_age=RECENT_AUTHENTICATION_WINDOW)


async def confirm_authentication(request: Request[Any, Any, Any], user: m.User, current_password: str | None) -> None:
    """Admit a sensitive action after a recent sign-in or a re-verified current password.

    A denial for a missing password reaches the client as a problem-details body whose top-level ``code``
    member is ``REAUTHENTICATION_REQUIRED``, so clients can prompt for the password and retry.

    Args:
        request: Request whose session evidence and client address are evaluated.
        user: Authenticated account performing the action.
        current_password: Current password re-confirming a sign-in older than ``RECENT_AUTHENTICATION_WINDOW``.

    Raises:
        PermissionDeniedException: If the sign-in is not recent and the current password is missing or wrong.
        TooManyRequestsException: If the account or client has exhausted its password verification attempts.
        ServiceUnavailableException: If the password cannot be verified.
    """
    if _recent_sign_in.decide(request).granted:
        return
    if not current_password:
        raise PermissionDeniedException(
            detail="Confirm your password to continue.",
            extra={"code": REAUTHENTICATION_REQUIRED},
        )
    local_auth = cast("SecurityPlugin[m.User]", request.app.plugins.get(SecurityPlugin)).config.local_auth
    if local_auth is None:
        raise ServiceUnavailableException(detail=_UNAVAILABLE)
    account_id = str(user.id)
    service = local_auth.local_auth_service
    limited = await local_auth.rate_limits.check(
        PASSWORD_VERIFY,
        client_key=service.client_key_for(request),
        identifier=account_id,
    )
    if isinstance(limited, RateLimited):
        headers = {"Retry-After": str(limited.retry_after)} if limited.retry_after is not None else None
        raise TooManyRequestsException(detail="Too many requests.", headers=headers)
    if limited is not None:
        raise ServiceUnavailableException(detail=_UNAVAILABLE)
    proof = await service.password_reauthentication.verify(account_id, current_password)
    if isinstance(proof, PasswordReauthenticationProof):
        return
    if isinstance(proof, VerificationUnavailable):
        raise ServiceUnavailableException(detail=_UNAVAILABLE)
    raise PermissionDeniedException(detail="The current password is incorrect.")
