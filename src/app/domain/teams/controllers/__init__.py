"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TCH002
from sqlalchemy.orm import joinedload, noload, subqueryload
from starlite import Body, Controller, MediaType, Provide, RequestEncodingType, Response, get, post

from app.domain import security, urls
from app.domain.teams import guards, schemas
from app.domain.teams.models import Team, TeamMember
from app.domain.teams.services import TeamService
from app.lib import log, orm

if TYPE_CHECKING:
    from starlite.contrib.jwt import OAuth2Login


logger = log.get_logger()


def provides_teams_service(db_session: AsyncSession) -> TeamService:
    """Construct repository and service objects for the request."""
    return TeamService(
        session=db_session,
        options=[
            noload("*"),
            subqueryload(Team.members).options(
                joinedload(TeamMember.team, innerjoin=True).options(
                    noload("*"),
                ),
            ),
        ],
    )


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
        user = await user_service.create(orm.model_from_dict(User, obj))
        return schemas.User.from_orm(user)

    @get(
        operation_id="AccountProfile",
        name="account:profile",
        path=urls.ACCOUNT_PROFILE,
        guards=[guards.requires_active_user],
        summary="User Profile",
        description="User profile information.",
    )
    async def profile(self, current_user: User) -> schemas.User:
        """User Profile."""
        return schemas.User.from_orm(current_user)
