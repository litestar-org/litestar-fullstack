"""User Account Controllers."""

from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, noload, subqueryload
from starlite import Controller, MediaType, Response, get, post
from starlite.contrib.jwt import OAuth2Login
from starlite.di import Provide
from starlite.enums import RequestEncodingType
from starlite.params import Body

from app.domain import security, urls
from app.domain.accounts import schemas
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.models import User
from app.domain.accounts.services import UserService
from app.domain.teams.models import TeamMember
from app.lib import log

logger = log.get_logger()


async def provides_user_service(db_session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Construct repository and service objects for the request."""
    async with UserService.new(
        session=db_session,
        base_select=select(User).options(
            noload("*"),
            subqueryload(User.teams).options(
                joinedload(TeamMember.team, innerjoin=True).options(
                    noload("*"),
                ),
            ),
        ),
    ) as service:
        try:
            yield service
        finally:
            ...


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {"user_service": Provide(provides_user_service)}

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
    async def profile(self, current_user: "User") -> schemas.User:
        """User Profile."""
        return current_user
