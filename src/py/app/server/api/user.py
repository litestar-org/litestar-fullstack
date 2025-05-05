"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app import schemas as s
from app.lib.deps import create_filter_dependencies
from app.server import deps, security

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination

    from app.services import UserService


class UserController(Controller):
    """User Account Controller."""

    path = "/api/users"
    tags = ["User Accounts"]
    guards = [security.requires_superuser]
    dependencies = {
        "users_service": Provide(deps.provide_users_service),
    } | create_filter_dependencies(
        {
            "id_filter": UUID,
            "search": "name,email",
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "sort_order": "asc",
        },
    )

    @get(operation_id="ListUsers")
    async def list_users(
        self, users_service: UserService, filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)]
    ) -> OffsetPagination[s.User]:
        """List users.

        Args:
            filters: The filters to apply to the list of users.
            users_service: The user service.

        Returns:
            The list of users.
        """
        results, total = await users_service.list_and_count(*filters)
        return users_service.to_schema(results, total, filters, schema_type=s.User)

    @get(operation_id="GetUser", path="/{user_id:uuid}")
    async def get_user(
        self,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to retrieve.")],
    ) -> s.User:
        """Get a user.

        Args:
            user_id: The ID of the user to retrieve.
            users_service: The user service.

        Returns:
            The user.
        """
        db_obj = await users_service.get(user_id)
        return users_service.to_schema(db_obj, schema_type=s.User)

    @post(operation_id="CreateUser")
    async def create_user(self, users_service: UserService, data: s.UserCreate) -> s.User:
        """Create a new user.

        Args:
            data: The data to create the user with.
            users_service: The user service.

        Returns:
            The created user.
        """
        db_obj = await users_service.create(data)
        return users_service.to_schema(db_obj, schema_type=s.User)

    @patch(operation_id="UpdateUser", path="/{user_id:uuid}")
    async def update_user(
        self,
        data: s.UserUpdate,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to update.")],
    ) -> s.User:
        """Update a user.

        Args:
            data: The data to update the user with.
            users_service: The user service.
            user_id: The ID of the user to update.

        Returns:
            The updated user.
        """
        db_obj = await users_service.update(item_id=user_id, data=data)
        return users_service.to_schema(db_obj, schema_type=s.User)

    @delete(operation_id="DeleteUser", path="/{user_id:uuid}")
    async def delete_user(
        self,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to delete.")],
    ) -> None:
        """Delete a user from the system.

        Args:
            user_id: The ID of the user to delete.
            users_service: The user service.
        """
        _ = await users_service.delete(user_id)
