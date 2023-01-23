from __future__ import annotations

from starlite import ASGIConnection, BaseRouteHandler, NotAuthorizedException

from app.lib import logging

logger = logging.getLogger()


__all__ = [
    "requires_superuser",
]


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
