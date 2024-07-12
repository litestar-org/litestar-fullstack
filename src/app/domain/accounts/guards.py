from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar.exceptions import PermissionDeniedException
from litestar.middleware.session.server_side import ServerSideSessionBackend
from litestar.security.jwt import OAuth2PasswordBearerAuth
from litestar.security.session_auth import SessionAuth
from litestar_vite.inertia import share

from app.config import constants
from app.config.app import alchemy
from app.config.app import session as session_config
from app.config.base import get_settings
from app.db.models import User
from app.domain.accounts import urls
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.schemas import User as UserSchema

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler
    from litestar.security.jwt import Token


__all__ = (
    "requires_superuser",
    "requires_active_user",
    "requires_verified_user",
    "current_user_from_token",
    "jwt_auth",
)


settings = get_settings()


def requires_active_user(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Request requires active user.

    Verifies the request user is active.

    Args:
        connection (ASGIConnection): HTTP Request
        _ (BaseRouteHandler): Route handler

    Raises:
        PermissionDeniedException: Permission denied exception
    """
    if connection.user.is_active:
        return
    msg = "Inactive account"
    raise PermissionDeniedException(msg)


def requires_superuser(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Request requires active superuser.

    Args:
        connection (ASGIConnection): HTTP Request
        _ (BaseRouteHandler): Route handler

    Raises:
        PermissionDeniedException: Permission denied exception

    Returns:
        None: Returns None when successful
    """
    if connection.user.is_superuser:
        return
    raise PermissionDeniedException(detail="Insufficient privileges")


def requires_verified_user(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user is a superuser.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized

    Returns:
        None: Returns None when successful
    """
    if connection.user.is_verified:
        return
    raise PermissionDeniedException(detail="User account is not verified.")


async def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> User | None:
    """Lookup current user from local JWT token.

    Fetches the user information from the database


    Args:
        token (str): JWT Token Object
        connection (ASGIConnection[Any, Any, Any, Any]): ASGI connection.


    Returns:
        User: User record mapped to the JWT identifier
    """
    service = await anext(provide_users_service(alchemy.provide_session(connection.app.state, connection.scope)))
    user = await service.get_one_or_none(email=token.sub)
    return user if user and user.is_active else None


async def current_user_from_session(
    session: dict[str, Any],
    connection: ASGIConnection[Any, Any, Any, Any],
) -> User | None:
    """Lookup current user from server session state.

    Fetches the user information from the database


    Args:
        session (dict[str,Any]): Litestar session dictionary
        connection (ASGIConnection[Any, Any, Any, Any]): ASGI connection.


    Returns:
        User: User record mapped to the JWT identifier
    """

    if (user_id := session.get("user_id")) is None:
        return None
    service = await anext(provide_users_service(alchemy.provide_session(connection.app.state, connection.scope)))
    user = await service.get_one_or_none(email=user_id)
    if user and user.is_active:
        share(connection, "auth", service.to_schema(user, schema_type=UserSchema))
        return user
    return None


session_auth = SessionAuth[User, ServerSideSessionBackend](
    session_backend_config=session_config,
    retrieve_user_handler=current_user_from_session,
    exclude=[
        constants.OPENAPI_SCHEMA,
        constants.HEALTH_ENDPOINT,
        urls.ACCOUNT_LOGIN,
        urls.ACCOUNT_REGISTER,
    ],
)

jwt_auth = OAuth2PasswordBearerAuth[User](
    retrieve_user_handler=current_user_from_token,
    token_secret=settings.app.SECRET_KEY,
    token_url=urls.ACCOUNT_LOGIN,
    exclude=[
        constants.OPENAPI_SCHEMA,
        constants.HEALTH_ENDPOINT,
        urls.ACCOUNT_LOGIN,
        urls.ACCOUNT_REGISTER,
    ],
)
