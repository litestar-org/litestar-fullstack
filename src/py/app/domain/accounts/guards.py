"""Account domain guards and authentication."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from litestar.exceptions import PermissionDeniedException
from litestar.security.jwt import OAuth2PasswordBearerAuth

from app.db import models as m
from app.domain.accounts import deps
from app.lib import constants
from app.lib.deps import provide_services
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from typing import Any

    from litestar.connection import ASGIConnection, Request
    from litestar.handlers.base import BaseRouteHandler
    from litestar.security.jwt import Token

settings = get_settings()
ACCESS_TOKEN_EXPIRATION = timedelta(minutes=15)
AUTH_TOKEN_URL = "/api/access/login"  # noqa: S105


def provide_user(request: Request[m.User, Token, Any]) -> m.User:
    """Get the user from the connection.

    Args:
        request: current connection.

    Returns:
        User
    """
    return request.user


def requires_active_user(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Request requires active user.

    Verifies the connection user is active.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized
    """
    if connection.user.is_active:
        return
    msg = "Inactive account"
    raise PermissionDeniedException(msg)


def requires_verified_user(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Verify the connection user is verified.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized
    """
    if connection.user.is_verified:
        return
    raise PermissionDeniedException(detail="User account is not verified.")


def requires_superuser(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Verify the connection user is a superuser.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized
    """
    if connection.user.is_superuser:
        return
    if any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
    ):
        return
    raise PermissionDeniedException(detail="Insufficient privileges")


async def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> m.User | None:
    """Lookup current user from local JWT token.

    Fetches the user information from the database

    Args:
        token (str): JWT Token Object
        connection (ASGIConnection[Any, Any, Any, Any]): ASGI connection.

    Returns:
        User: User record mapped to the JWT identifier
    """
    async with provide_services(deps.provide_users_service, connection=connection) as (service,):
        user = await service.get_one_or_none(email=token.sub)
        return user if user and user.is_active else None


def create_access_token(
    user_id: str,
    email: str,
    is_superuser: bool = False,
    is_verified: bool = False,
    auth_method: str = "password",
    amr: list[str] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID
        email: User email
        is_superuser: Whether user is superuser
        is_verified: Whether user email is verified
        auth_method: Authentication method used
        amr: Authentication methods reference for the token

    Returns:
        JWT token string
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    from litestar.security.jwt import Token

    if amr is None:
        amr = ["pwd"] if auth_method == "password" else [auth_method]
    token = Token(
        sub=email,
        exp=datetime.now(UTC) + ACCESS_TOKEN_EXPIRATION,
        jti=str(uuid4()),
        extras={
            "user_id": user_id,
            "is_superuser": is_superuser,
            "is_verified": is_verified,
            "auth_method": auth_method,
            "amr": amr,
        },
    )
    return token.encode(secret=settings.app.SECRET_KEY, algorithm=settings.app.JWT_ENCRYPTION_ALGORITHM)


auth = OAuth2PasswordBearerAuth[m.User](
    retrieve_user_handler=current_user_from_token,
    token_secret=settings.app.SECRET_KEY,
    token_url=AUTH_TOKEN_URL,
    default_token_expiration=ACCESS_TOKEN_EXPIRATION,
    exclude=[
        "/health",
        "/api/access/login",
        "/api/access/logout",
        "/api/access/signup",
        "/api/access/refresh",
        "/api/access/forgot-password",
        "/api/access/reset-password",
        "/api/email-verification/*",
        "/api/auth/oauth/*",
        "^/schema",
        "^/public/",
    ],
)
"""OAuth2 JWT Authentication."""

__all__ = (
    "auth",
    "create_access_token",
    "current_user_from_token",
    "provide_user",
    "requires_active_user",
    "requires_superuser",
    "requires_verified_user",
)
