"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar import Controller, MediaType, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body

from app.domain import security, urls
from app.domain.accounts import schemas
from app.domain.accounts.dependencies import provides_user_analytic_queries, provides_user_service
from app.domain.accounts.guards import requires_active_user
from app.lib import log

__all__ = ["AccessController", "provides_user_service"]


logger = log.get_logger()

if TYPE_CHECKING:
    from litestar.contrib.jwt import OAuth2Login

    from app.domain.accounts.models import User
    from app.domain.accounts.services import UserAnalyticQueryManager, UserService


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {
        "user_service": Provide(provides_user_service),
        "user_analytics_service": Provide(provides_user_analytic_queries),
    }

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
        user_service: UserService,
        data: schemas.UserLogin = Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED),
    ) -> Response[OAuth2Login]:
        """Authenticate a user."""
        user = await user_service.authenticate(data.username, data.password)
        return security.auth.login(user.email)

    @post(
        operation_id="AccountRegister",
        name="account:register",
        path=urls.ACCOUNT_REGISTER,
        cache=False,
        summary="Create User",
        description="Register a new account.",
    )
    async def signup(self, user_service: UserService, data: schemas.UserRegister) -> schemas.User:
        """User Signup."""
        obj = data.dict(exclude_unset=True, by_alias=False, exclude_none=True)
        user = await user_service.create(obj)
        return schemas.User.from_orm(user)

    @get(
        operation_id="AccountProfile",
        name="account:profile",
        path=urls.ACCOUNT_PROFILE,
        guards=[requires_active_user],
        summary="User Profile",
        description="User profile information.",
    )
    async def profile(self, current_user: User) -> schemas.User:
        """User Profile."""
        return schemas.User.from_orm(current_user)

    @get(operation_id="AccountQuery", name="account:query-test", path="/test", opt={"exclude_from_auth": True})
    async def users_by_week(self, user_analytics_service: UserAnalyticQueryManager) -> dict[str, Any]:
        """Users by week."""
        return await user_analytics_service.users_by_week()
