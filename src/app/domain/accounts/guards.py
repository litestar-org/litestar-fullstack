from __future__ import annotations

from typing import TYPE_CHECKING

from starlite.exceptions import NotAuthorizedException

if TYPE_CHECKING:
    from starlite.connection import ASGIConnection
    from starlite.handlers.base import BaseRouteHandler


__all__ = ["requires_superuser", "requires_active_user"]


def requires_active_user(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Request requires active user.

    Verifies the request user is active.

    Args:
        connection (ASGIConnection): HTTP Request
        _ (BaseRouteHandler): Route handler

    Raises:
        NotAuthorizedException: Not authorized exception
    """
    if connection.user.is_active:
        return
    raise NotAuthorizedException("Inactive account")


def requires_superuser(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Request requires active superuser.

    Args:
        connection (ASGIConnection): HTTP Request
        _ (BaseRouteHandler): Route handler

    Raises:
        NotAuthorizedException: Not authorized exception

    Returns:
        None: No Return
    """
    if connection.user.is_superuser:
        return
    raise NotAuthorizedException(detail="Insufficient privileges")
