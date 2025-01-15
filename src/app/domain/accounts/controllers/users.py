"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app.domain.accounts import urls
from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.schemas import User, UserCreate, UserUpdate

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination

    from app.domain.accounts.services import UserService


class UserController(Controller):
    """User Account Controller."""

    tags = ["User Accounts"]
    guards = [requires_superuser]
    dependencies = {
        "users_service": Provide(provide_users_service),
    }

    @get(operation_id="ListUsers", path=urls.ACCOUNT_LIST, cache=60)
    async def list_users(
        self,
        users_service: UserService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[User]:
        """List users."""
        results, total = await users_service.list_and_count(*filters)
        return users_service.to_schema(data=results, total=total, schema_type=User, filters=filters)

    @get(operation_id="GetUser", path=urls.ACCOUNT_DETAIL)
    async def get_user(
        self,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to retrieve.")],
    ) -> User:
        """Get a user."""
        db_obj = await users_service.get(user_id)
        return users_service.to_schema(db_obj, schema_type=User)

    @post(operation_id="CreateUser", path=urls.ACCOUNT_CREATE)
    async def create_user(self, users_service: UserService, data: UserCreate) -> User:
        """Create a new user."""
        db_obj = await users_service.create(data.to_dict())
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(operation_id="UpdateUser", path=urls.ACCOUNT_UPDATE)
    async def update_user(
        self,
        data: UserUpdate,
        users_service: UserService,
        user_id: UUID = Parameter(title="User ID", description="The user to update."),
    ) -> User:
        """Create a new user."""
        db_obj = await users_service.update(item_id=user_id, data=data.to_dict())
        return users_service.to_schema(db_obj, schema_type=User)

    @delete(operation_id="DeleteUser", path=urls.ACCOUNT_DELETE)
    async def delete_user(
        self,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to delete.")],
    ) -> None:
        """Delete a user from the system."""
        _ = await users_service.delete(user_id)
