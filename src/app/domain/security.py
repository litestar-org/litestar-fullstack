from __future__ import annotations

from typing import Any

from starlite import ASGIConnection
from starlite.contrib.jwt import OAuth2PasswordBearerAuth, Token

from app.domain import urls
from app.domain.accounts.models import User
from app.domain.accounts.services import UserService
from app.lib import settings

__all__ = ["current_user_from_token", "auth"]


async def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any]) -> User | None:
    """Lookup current user from local JWT token.

    Fetches the user information from the database when loading from a local token.

    If the user doesn't exist, the record will be created and returned.

    Args:
        token (str): JWT Token Object
        connection (ASGIConnection[Any, Any, Any]): ASGI connection.


    Returns:
        User: User record mapped to the JWT identifier
    """
    service = UserService()
    user = await service.get_by_email(token.sub)
    if user and user.is_active:
        return user
    return None


auth = OAuth2PasswordBearerAuth[User](
    retrieve_user_handler=current_user_from_token,
    token_secret=settings.app.SECRET_KEY.get_secret_value().decode(),
    token_url=urls.ACCOUNT_LOGIN,
    exclude=[
        urls.OPENAPI_SCHEMA,
        urls.SYSTEM_HEALTH,
        urls.ACCOUNT_LOGIN,
        urls.ACCOUNT_REGISTER,
    ],
)
