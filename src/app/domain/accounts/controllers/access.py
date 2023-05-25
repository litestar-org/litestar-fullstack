"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, MediaType, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body

from app.domain import security, urls
from app.domain.accounts import schemas
from app.domain.accounts.dependencies import provides_user_service
from app.domain.accounts.guards import requires_active_user
from app.lib import log

__all__ = ["AccessController", "provides_user_service"]


logger = log.get_logger()

if TYPE_CHECKING:
    from litestar.contrib.jwt import OAuth2Login

    from app.domain.accounts.models import User
    from app.domain.accounts.services import UserService


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {"users_service": Provide(provides_user_service)}

    @post(
        operation_id="AccountLogin",
        name="account:login",
        path=urls.ACCOUNT_LOGIN,
        media_type=MediaType.JSON,
        cache=False,
        summary="Login",
    )
    async def login(
        self,
        users_service: UserService,
        data: schemas.UserLogin = Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED),
    ) -> Response[OAuth2Login]:
        """Authenticate a user."""
        user = await users_service.authenticate(data.username, data.password)
        return security.auth.login(user.email)

    @post(
        operation_id="AccountRegister",
        name="account:register",
        path=urls.ACCOUNT_REGISTER,
        cache=False,
        summary="Create User",
        description="Register a new account.",
    )
    async def signup(self, users_service: UserService, data: schemas.UserRegister) -> schemas.User:
        """User Signup."""
        obj = data.dict(exclude_unset=True, by_alias=False, exclude_none=True)
        user = await users_service.create(obj)
        return users_service.to_dto(schemas.User, user)

    @get(
        operation_id="AccountProfile",
        name="account:profile",
        path=urls.ACCOUNT_PROFILE,
        guards=[requires_active_user],
        summary="User Profile",
        description="User profile information.",
    )
    async def profile(self, current_user: User, users_service: UserService) -> schemas.User:
        """User Profile."""
        return users_service.to_dto(schemas.User, current_user)
