from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.exceptions import PermissionDeniedException

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler


__all__ = ["requires_superuser", "requires_active_user", "requires_verified_user"]


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
