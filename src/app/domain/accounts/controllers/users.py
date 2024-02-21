"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from msgspec.structs import asdict

from app.domain import urls
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.dtos import UserCreate, UserDTO, UserUpdate
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.services import UserService

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from litestar.pagination import OffsetPagination
    from uuid_utils import UUID

    from app.db.models import User


class UserController(Controller):
    """User Account Controller."""

    tags = ["User Accounts"]
    guards = [requires_superuser]
    dependencies = {"users_service": Provide(provide_users_service)}
    return_dto = UserDTO
    signature_namespace = {"UserService": UserService}

    @get(
        operation_id="ListUsers",
        name="users:list",
        summary="List Users",
        description="Retrieve the users.",
        path=urls.ACCOUNT_LIST,
        cache=60,
    )
    async def list_users(
        self,
        users_service: UserService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
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
        user_id: Annotated[
            UUID,
            Parameter(
                title="User ID",
                description="The user to retrieve.",
            ),
        ],
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
    )
    async def create_user(
        self,
        users_service: UserService,
        data: UserCreate,
    ) -> User:
        """Create a new user."""
        db_obj = await users_service.create(asdict(data))
        return users_service.to_dto(db_obj)

    @patch(
        operation_id="UpdateUser",
        name="users:update",
        path=urls.ACCOUNT_UPDATE,
    )
    async def update_user(
        self,
        data: UserUpdate,
        users_service: UserService,
        user_id: UUID = Parameter(
            title="User ID",
            description="The user to update.",
        ),
    ) -> User:
        """Create a new user."""
        db_obj = await users_service.update(item_id=user_id, data=asdict(data))
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
        user_id: Annotated[
            UUID,
            Parameter(
                title="User ID",
                description="The user to delete.",
            ),
        ],
    ) -> None:
        """Delete a user from the system."""
        _ = await users_service.delete(user_id)
