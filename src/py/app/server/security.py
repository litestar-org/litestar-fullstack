from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.exceptions import PermissionDeniedException
from litestar.security.jwt import OAuth2PasswordBearerAuth

from app import config
from app.db import models as m
from app.lib import constants
from app.lib.settings import get_settings
from app.server import deps

if TYPE_CHECKING:
    from typing import Any

    from litestar.connection import ASGIConnection, Request
    from litestar.handlers.base import BaseRouteHandler
    from litestar.security.jwt import Token

settings = get_settings()


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


def requires_team_membership(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Verify the connection user is a member of the team.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized

    """
    team_id = connection.path_params["team_id"]
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
    )
    has_team_role = any(membership.team.id == team_id for membership in connection.user.teams)
    if connection.user.is_superuser or has_system_role or has_team_role:
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access team.")


def requires_team_admin(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Verify the connection user is a team admin.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized

    """
    team_id = connection.path_params["team_id"]
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
    )
    has_team_role = any(
        membership.team.id == team_id and membership.role == m.TeamRoles.ADMIN for membership in connection.user.teams
    )
    if connection.user.is_superuser or has_system_role or has_team_role:
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access team.")


def requires_team_ownership(connection: ASGIConnection[Any, m.User, Token, Any], _: BaseRouteHandler) -> None:
    """Verify that the connection user is the team owner.

    Args:
        connection (ASGIConnection): Request/Connection object.
        _ (BaseRouteHandler): Route handler.

    Raises:
        PermissionDeniedException: Not authorized

    """
    team_id = connection.path_params["team_id"]
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
    )
    has_team_role = any(membership.team.id == team_id and membership.is_owner for membership in connection.user.teams)
    if connection.user.is_superuser or has_system_role or has_team_role:
        return

    msg = "Insufficient permissions to access team."
    raise PermissionDeniedException(msg)


async def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> m.User | None:
    """Lookup current user from local JWT token.

    Fetches the user information from the database


    Args:
        token (str): JWT Token Object
        connection (ASGIConnection[Any, Any, Any, Any]): ASGI connection.


    Returns:
        User: User record mapped to the JWT identifier
    """
    service = await anext(
        deps.provide_users_service(config.alchemy.provide_session(connection.app.state, connection.scope))
    )
    user = await service.get_one_or_none(email=token.sub)
    return user if user and user.is_active else None


def create_access_token(
    user_id: str,
    email: str,
    is_superuser: bool = False,
    is_verified: bool = False,
    auth_method: str = "password",
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID
        email: User email
        is_superuser: Whether user is superuser
        is_verified: Whether user email is verified
        auth_method: Authentication method used

    Returns:
        JWT token string
    """
    from datetime import UTC, datetime, timedelta

    from litestar.security.jwt import Token

    token = Token(
        sub=email,
        exp=datetime.now(UTC) + timedelta(hours=1),  # 1 hour expiration
        extras={
            "user_id": user_id,
            "is_superuser": is_superuser,
            "is_verified": is_verified,
            "auth_method": auth_method,
        },
    )
    return token.encode(secret=settings.app.SECRET_KEY, algorithm=settings.app.JWT_ENCRYPTION_ALGORITHM)


auth = OAuth2PasswordBearerAuth[m.User](
    retrieve_user_handler=current_user_from_token,
    token_secret=settings.app.SECRET_KEY,
    token_url="/api/access/login",  # noqa: S106
    exclude=[
        "/api/health",
        "/api/access/login",
        "/api/access/signup",
        "/api/access/forgot-password",
        "/api/access/reset-password",
        "/api/email-verification/*",
        "/api/auth/oauth/*",
        "^/schema",
        "^/public/",
    ],
)
"""OAuth2 JWT Authentication."""
