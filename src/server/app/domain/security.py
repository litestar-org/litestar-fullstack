from __future__ import annotations

from typing import TYPE_CHECKING

from starlite import ASGIConnection, NotAuthorizedException
from starlite.contrib.jwt import Token

from app.domain.accounts.services import UserService
from app.lib import logging

if TYPE_CHECKING:
    from typing import Any

    from app.domain.accounts.models import User

logger = logging.getLogger()


__all__ = ["current_user_from_token"]


async def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any]) -> User:
    """Lookup current user from local JWT token.

    Fetches the user information from the database when loading from a local token.

    If the user doesn't exist, the record will be created and returned.

    Args:
        token (str): JWT Token Object
        connection (ASGIConnection[Any, Any, Any]): ASGI connection.

    Raises:
        NotAuthorizedException: User not authorized.

    Returns:
        User: User record mapped to the JWT identifier
    """
    service = UserService()
    user = await service.get(token.sub)
    if user and user.is_active:
        return user
    raise NotAuthorizedException("Unable to authenticate token.")
