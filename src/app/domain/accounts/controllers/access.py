"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, MediaType, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType  # noqa: TCH002
from litestar.params import Body  # noqa: TCH002
from litestar.security.jwt import OAuth2Login

from app.domain import security, urls
from app.domain.accounts.dependencies import provides_user_service
from app.domain.accounts.dtos import AccountLogin, AccountLoginDTO, AccountRegister, AccountRegisterDTO, UserDTO
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.models import User
from app.domain.accounts.services import UserService
from app.lib import log

__all__ = ["AccessController", "provides_user_service"]


logger = log.get_logger()

if TYPE_CHECKING:
    from litestar.dto import DTOData


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {"users_service": Provide(provides_user_service)}
    signature_namespace = {"UserService": UserService, "User": User, "OAuth2Login": OAuth2Login}

    return_dto = UserDTO

    @post(
        operation_id="AccountLogin",
        name="account:login",
        path=urls.ACCOUNT_LOGIN,
        media_type=MediaType.JSON,
        cache=False,
        summary="Login",
        dto=AccountLoginDTO,
        return_dto=None,
    )
    async def login(
        self,
        users_service: UserService,
        data: Annotated[DTOData[AccountLogin], Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response[OAuth2Login]:
        """Authenticate a user."""
        obj = data.create_instance()
        user = await users_service.authenticate(obj.username, obj.password)
        return security.auth.login(user.email)

    @post(
        operation_id="AccountRegister",
        name="account:register",
        path=urls.ACCOUNT_REGISTER,
        cache=False,
        summary="Create User",
        description="Register a new account.",
        dto=AccountRegisterDTO,
    )
    async def signup(self, users_service: UserService, data: DTOData[AccountRegister]) -> User:
        """User Signup."""
        user = await users_service.create(data.as_builtins())
        return users_service.to_dto(user)

    @get(
        operation_id="AccountProfile",
        name="account:profile",
        path=urls.ACCOUNT_PROFILE,
        guards=[requires_active_user],
        summary="User Profile",
        description="User profile information.",
    )
    async def profile(self, current_user: User, users_service: UserService) -> User:
        """User Profile."""
        return users_service.to_dto(current_user)
