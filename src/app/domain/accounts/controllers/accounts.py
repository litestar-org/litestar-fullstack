"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app.domain import urls
from app.domain.accounts.dependencies import provides_user_service
from app.domain.accounts.dtos import UserCreate, UserCreateDTO, UserDTO, UserUpdate, UserUpdateDTO
from app.domain.accounts.guards import requires_superuser
from app.lib import log

__all__ = ["AccountController"]


if TYPE_CHECKING:
    from uuid import UUID

    from litestar.contrib.repository.filters import FilterTypes
    from litestar.dto import DTOData
    from litestar.pagination import OffsetPagination

    from app.domain.accounts.models import User
    from app.domain.accounts.services import UserService


logger = log.get_logger()


class AccountController(Controller):
    """Account Controller."""

    tags = ["User Accounts"]
    guards = [requires_superuser]
    dependencies = {"users_service": Provide(provides_user_service)}
    return_dto = UserDTO

    @get(
        operation_id="ListUsers",
        name="users:list",
        summary="List Users",
        description="Retrieve the users.",
        path=urls.ACCOUNT_LIST,
        cache=60,
    )
    async def list_users(
        self, users_service: UserService, filters: list[FilterTypes] = Dependency(skip_validation=True)
    ) -> OffsetPagination[User]:
        """List users."""
        results, total = await users_service.list_and_count(*filters)
        return users_service.to_dto(results, total, *filters)

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
    ) -> User:
        """Get a user."""
        db_obj = await users_service.get(user_id)
        return users_service.to_dto(db_obj)

    @post(
        operation_id="CreateUser",
        name="users:create",
        summary="Create a new user.",
        cache_control=None,
        description="A user who can login and use the system.",
        path=urls.ACCOUNT_CREATE,
        dto=UserCreateDTO,
    )
    async def create_user(
        self,
        users_service: UserService,
        data: DTOData[UserCreate],
    ) -> User:
        """Create a new user."""
        obj = data.create_instance()
        db_obj = await users_service.create(obj.__dict__)
        return users_service.to_dto(db_obj)

    @patch(
        operation_id="UpdateUser",
        name="users:update",
        path=urls.ACCOUNT_UPDATE,
        dto=UserUpdateDTO,
    )
    async def update_user(
        self,
        data: DTOData[UserUpdate],
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to update.",
        ),
    ) -> User:
        """Create a new user."""
        db_obj = await users_service.update(user_id, data.as_builtins())
        return users_service.to_dto(db_obj)

    @delete(
        operation_id="DeleteUser",
        name="users:delete",
        path=urls.ACCOUNT_DELETE,
        summary="Remove User",
        description="Removes a user and all associated data from the system.",
        return_dto=None,
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
