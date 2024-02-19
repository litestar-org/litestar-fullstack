"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, Request, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.security.jwt import OAuth2Login
from msgspec.structs import asdict

from app.domain import security, urls
from app.domain.accounts.dependencies import provide_roles_service, provide_users_service
from app.domain.accounts.dtos import AccountLogin, AccountRegister, UserDTO
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.services import RoleService, UserService
from app.utils import slugify

if TYPE_CHECKING:
    from app.db.models import User


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {"users_service": Provide(provide_users_service), "roles_service": Provide(provide_roles_service)}
    signature_namespace = {
        "UserService": UserService,
        "RoleService": RoleService,
        "OAuth2Login": OAuth2Login,
        "RequestEncodingType": RequestEncodingType,
        "Body": Body,
        "AccountLogin": AccountLogin,
    }
    return_dto = UserDTO

    @post(
        operation_id="AccountLogin",
        name="account:login",
        path=urls.ACCOUNT_LOGIN,
        cache=False,
        summary="Login",
        dto=None,
        return_dto=None,
        exclude_from_auth=True,
    )
    async def login(
        self,
        users_service: UserService,
        data: Annotated[AccountLogin, Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response[OAuth2Login]:
        """Authenticate a user."""
        user = await users_service.authenticate(data.username, data.password)
        return security.auth.login(user.email)

    @post(
        operation_id="AccountLogout",
        name="account:logout",
        path=urls.ACCOUNT_LOGOUT,
        cache=False,
        summary="Logout",
        dto=None,
        return_dto=None,
        exclude_from_auth=True,
    )
    async def logout(
        self,
        request: Request,
    ) -> None:
        """Account Logout"""
        request.cookies.pop(security.auth.key, None)
        request.clear_session()

    @post(
        operation_id="AccountRegister",
        name="account:register",
        path=urls.ACCOUNT_REGISTER,
        cache=False,
        summary="Create User",
        description="Register a new account.",
        dto=None,
    )
    async def signup(
        self,
        request: Request,
        users_service: UserService,
        roles_service: RoleService,
        data: AccountRegister,
    ) -> User:
        """User Signup."""
        user_data = asdict(data)
        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})
        user = await users_service.create(user_data)
        request.app.emit(event_id="user_created", user_id=user.id)
        return users_service.to_dto(user)

    @get(
        operation_id="AccountProfile",
        name="account:profile",
        path=urls.ACCOUNT_PROFILE,
        guards=[requires_active_user],
        summary="User Profile",
        description="User profile information.",
    )
    async def profile(self, request: Request, current_user: User, users_service: UserService) -> User:
        """User Profile."""
        return users_service.to_dto(current_user)
