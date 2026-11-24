"""User account administration SecureController."""

from typing import Annotated, ClassVar
from uuid import UUID

from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service import OffsetPagination
from litestar import delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar_security import AuthenticationPolicy, SecureController, required, requires_role

from app.domain.accounts.deps import UserFilterSet, create_filter_dependencies, provide_users_service
from app.domain.accounts.schemas import User, UserCreate, UserUpdate
from app.domain.accounts.services import UserService


class UserController(SecureController):
    """Superuser CRUD controller for user accounts."""

    path = "/api/users"
    tags = ["User Accounts"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    guards = [requires_role("superuser")]
    dependencies = {
        "users_service": Provide(provide_users_service),
        **create_filter_dependencies(UserFilterSet),
    }

    @get(operation_id="ListUsers")
    async def list_users(
        self,
        users_service: UserService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[User]:
        """List user accounts using Advanced Alchemy filters."""
        results, total = await users_service.get_many_and_count(*filters)
        return users_service.to_schema(results, total, filters=filters, schema_type=User)

    @get(operation_id="GetUser", path="/{user_id:uuid}")
    async def get_user(
        self,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to retrieve.")],
    ) -> User:
        """Retrieve a single user account by UUID."""
        db_obj = await users_service.get(user_id)
        return users_service.to_schema(db_obj, schema_type=User)

    @post(operation_id="CreateUser")
    async def create_user(self, users_service: UserService, data: UserCreate) -> User:
        """Create a new user account."""
        db_obj = await users_service.create(data.to_dict(), auto_commit=True)
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(operation_id="UpdateUser", path="/{user_id:uuid}")
    async def update_user(
        self,
        data: UserUpdate,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to update.")],
    ) -> User:
        """Partially update an existing user account."""
        db_obj = await users_service.update(item_id=user_id, data=data.to_dict(), auto_commit=True)
        return users_service.to_schema(db_obj, schema_type=User)

    @delete(operation_id="DeleteUser", path="/{user_id:uuid}")
    async def delete_user(
        self,
        users_service: UserService,
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to delete.")],
    ) -> None:
        """Delete a user account by UUID."""
        _ = await users_service.delete(user_id, auto_commit=True)
