"""User Access Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body

from app import schemas as s
from app.lib.deps import create_service_provider
from app.server import deps, security
from app.services import RoleService, UserService

if TYPE_CHECKING:
    from litestar.security.jwt import OAuth2Login, Token

    from app.db import models as m


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {
        "users_service": Provide(deps.provide_users_service),
        "roles_service": Provide(create_service_provider(RoleService)),
    }

    @post(operation_id="AccountLogin", path="/api/access/login", exclude_from_auth=True)
    async def login(
        self,
        users_service: UserService,
        data: Annotated[s.AccountLogin, Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response[OAuth2Login]:
        """Authenticate a user.

        Args:
            data: OAuth2 Login Data
            users_service: User Service

        Returns:
            OAuth2 Login Response
        """
        user = await users_service.authenticate(data.username, data.password)
        return security.auth.login(user.email)

    @post(operation_id="AccountLogout", path="/api/access/logout", exclude_from_auth=True)
    async def logout(self, request: Request[m.User, Token, Any]) -> Response[s.Message]:
        """Account Logout

        Args:
            request: Request

        Returns:
            Logout Response
        """
        request.cookies.pop(security.auth.key, None)
        request.clear_session()
        response = Response(s.Message(message="OK"), status_code=200)
        response.delete_cookie(security.auth.key)
        return response

    @post(operation_id="AccountRegister", path="/api/access/signup")
    async def signup(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        roles_service: RoleService,
        data: s.AccountRegister,
    ) -> s.User:
        """User Signup.

        Args:
            request: Request
            users_service: User Service
            roles_service: Role Service
            data: Account Register Data

        Returns:
            User
        """
        user_data = data.to_dict()
        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})
        user = await users_service.create(user_data)
        request.app.emit(event_id="user_created", user_id=user.id)
        return users_service.to_schema(user, schema_type=s.User)
