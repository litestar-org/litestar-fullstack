from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy import select
from sqlalchemy.orm import joinedload, noload, selectinload
from starlite.contrib.jwt import OAuth2PasswordBearerAuth, Token

from app.domain import urls
from app.domain.accounts.models import User
from app.domain.accounts.services import UserService
from app.domain.teams.models import TeamMember
from app.lib import settings

__all__ = ["current_user_from_token", "auth"]

if TYPE_CHECKING:
    from starlite.connection import ASGIConnection, Request


async def provide_user(request: Request) -> User:
    """Get the user from the connection.

    Args:
        request: current connection.

    Returns:
    User | None
    """
    return cast("User", request.user)


async def current_user_from_token(token: Token, connection: ASGIConnection) -> User | None:
    """Lookup current user from JWT token.

    Fetches the user information from the database


    Args:
        token (str): JWT Token Object
        connection (ASGIConnection): ASGI connection.


    Returns:
        User: User record mapped to the JWT identifier
    """
    async with UserService.new(
        base_select=select(User).options(
            noload("*"),
            selectinload(User.teams).options(
                joinedload(TeamMember.team, innerjoin=True).options(
                    noload("*"),
                ),
            ),
        ),
    ) as service:
        user = await service.get_one_or_none(email=token.sub)
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
