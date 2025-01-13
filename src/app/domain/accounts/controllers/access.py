"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, get, post
from litestar.enums import RequestEncodingType
from litestar.params import Body

from app.domain.accounts import urls
from app.domain.accounts.guards import auth, requires_active_user
from app.domain.accounts.schemas import AccountLogin, AccountRegister, User

if TYPE_CHECKING:
    from litestar.security.jwt import OAuth2Login

    from app.db import models as m
    from app.domain.accounts.services import RoleService, UserService


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]

    @post(operation_id="AccountLogin", path=urls.ACCOUNT_LOGIN, exclude_from_auth=True)
    async def login(
        self,
        users_service: UserService,
        data: Annotated[AccountLogin, Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response[OAuth2Login]:
        """Authenticate a user."""
        user = await users_service.authenticate(data.username, data.password)
        return auth.login(user.email)

    @post(operation_id="AccountLogout", path=urls.ACCOUNT_LOGOUT, exclude_from_auth=True)
    async def logout(self, request: Request) -> Response:
        """Account Logout"""
        request.cookies.pop(auth.key, None)
        request.clear_session()

        response = Response(
            {"message": "OK"},
            status_code=200,
        )
        response.delete_cookie(auth.key)

        return response

    @post(operation_id="AccountRegister", path=urls.ACCOUNT_REGISTER)
    async def signup(
        self,
        request: Request,
        users_service: UserService,
        roles_service: RoleService,
        data: AccountRegister,
    ) -> User:
        """User Signup."""
        user_data = data.to_dict()
        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})
        user = await users_service.create(user_data)
        request.app.emit(event_id="user_created", user_id=user.id)
        return users_service.to_schema(user, schema_type=User)

    @get(operation_id="AccountProfile", path=urls.ACCOUNT_PROFILE, guards=[requires_active_user])
    async def profile(self, current_user: m.User, users_service: UserService) -> User:
        """User Profile."""
        return users_service.to_schema(current_user, schema_type=User)
