"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, Request, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.security.jwt import OAuth2Login

from app.domain import security, urls
from app.domain.accounts.dependencies import provide_roles_service, provide_users_service
from app.domain.accounts.dtos import AccountLogin, AccountLoginDTO, AccountRegister, AccountRegisterDTO, UserDTO
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.services import RoleService, UserService
from app.utils import slugify

if TYPE_CHECKING:
    from litestar.dto import DTOData

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
    }
    return_dto = UserDTO

    @post(
        operation_id="AccountLogin",
        name="account:login",
        path=urls.ACCOUNT_LOGIN,
        cache=False,
        summary="Login",
        dto=AccountLoginDTO,
        return_dto=None,
        exclude_from_auth=True,
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
        dto=AccountRegisterDTO,
    )
    async def signup(
        self,
        request: Request,
        users_service: UserService,
        roles_service: RoleService,
        data: DTOData[AccountRegister],
    ) -> User:
        """User Signup."""
        user_data = data.as_builtins()
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
