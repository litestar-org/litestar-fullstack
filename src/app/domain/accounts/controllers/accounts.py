"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import parse_obj_as
from sqlalchemy import select
from sqlalchemy.orm import joinedload, noload, subqueryload
from starlite import Controller, delete, get, patch, post
from starlite.di import Provide
from starlite.enums import RequestEncodingType
from starlite.pagination import OffsetPagination
from starlite.params import Body, Dependency, Parameter

from app.domain import urls
from app.domain.accounts import schemas
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.models import User
from app.domain.accounts.services import UserService
from app.domain.teams.models import TeamMember
from app.lib import log

__all__ = ["AccountController", "provide_users_service"]


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from starlite.contrib.repository.abc import FilterTypes


logger = log.get_logger()


async def provide_users_service(db_session: AsyncSession) -> AsyncGenerator[UserService, None]:
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


class AccountController(Controller):
    """Account Controller."""

    tags = ["User Accounts"]
    guards = [requires_superuser]
    dependencies = {"users_service": Provide(provide_users_service)}

    @get(
        operation_id="ListUsers",
        name="users:list",
        summary="List Users",
        description="Retrieve the users.",
        path=urls.ACCOUNT_LIST,
    )
    async def list_users(
        self, users_service: UserService, filters: list[FilterTypes] = Dependency(skip_validation=True)
    ) -> OffsetPagination[schemas.User]:
        """Create a new migration tag."""
        """List collections for a workspace."""
        results, total = await users_service.list_and_count(*filters)
        limit_offset = users_service._limit_offset(*filters)
        return OffsetPagination[schemas.User](
            items=parse_obj_as(list[schemas.User], results),
            total=total,
            limit=limit_offset.limit,
            offset=limit_offset.offset,
        )

    @post(
        operation_id="CreateUser",
        name="users:create",
        summary="Create a new user.",
        cache_control=None,
        description="A user who can login and use the system.",
        path=urls.ACCOUNT_CREATE,
    )
    async def create_user(
        self,
        users_service: UserService,
        data: schemas.UserCreate = Body(media_type=RequestEncodingType.MULTI_PART),
    ) -> schemas.User:
        """Create a new migration user."""
        db_obj = await users_service.create(data.dict(exclude_unset=True, by_alias=False, exclude_none=True))
        return schemas.User.from_orm(db_obj)

    @get(
        operation_id="GetUser",
        name="users:get",
        path=urls.ACCOUNT_DETAIL,
        summary="Retrieve the details of a user.",
    )
    async def get_user(
        self,
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to retrieve.",
        ),
    ) -> schemas.User:
        """Get a new migration user."""
        db_obj = await users_service.get(user_id)
        return schemas.User.from_orm(db_obj)

    @patch(operation_id="UpdateUser", name="users:update", path=urls.ACCOUNT_UPDATE)
    async def update_user(
        self,
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to update.",
        ),
        data: schemas.UserCreate = Body(media_type=RequestEncodingType.MULTI_PART),
    ) -> schemas.User:
        """Create a new migration user."""
        db_obj = await users_service.update(user_id, data.dict(exclude_unset=True, by_alias=False, exclude_none=True))
        return schemas.User.from_orm(db_obj)

    @delete(
        operation_id="DeleteUser",
        name="users:delete",
        path=urls.ACCOUNT_DELETE,
        summary="Remove User",
        description="Removes a user and all associated data from the system. Deleting a user is permanent, so please be sure you know what you are doing!",
    )
    async def delete_user(
        self,
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to delete.",
        ),
    ) -> None:
        """Delete a user from the system."""
        _ = await users_service.delete(user_id)
