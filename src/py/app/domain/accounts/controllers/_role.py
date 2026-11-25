"""Role administration SecureController."""

from typing import Annotated, ClassVar
from uuid import UUID

from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service import OffsetPagination
from litestar import delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Dependency, Parameter
from litestar_security import AuthenticationPolicy, CurrentUser, SecureController, required, requires_role

from app.db import models as m
from app.domain.accounts.deps import (
    RoleFilterSet,
    create_filter_dependencies,
    provide_account_services,
    provide_roles_service,
)
from app.domain.accounts.schemas import Message, Role, RoleCreate, RoleUpdate, UserRoleAdd, UserRoleRevoke
from app.domain.accounts.services import AccountServices, RoleService
from app.lib.constants import DEFAULT_ACCESS_ROLE, SUPERUSER_ACCESS_ROLE

_PROTECTED_ROLES = frozenset({DEFAULT_ACCESS_ROLE, SUPERUSER_ACCESS_ROLE})


class RoleController(SecureController):
    """Superuser controller for role management and atomic role assignment."""

    path = "/api/roles"
    tags = ["Roles"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    guards = [requires_role("superuser")]
    dependencies = {
        "roles_service": Provide(provide_roles_service),
        "account_services": Provide(provide_account_services),
        **create_filter_dependencies(RoleFilterSet),
    }

    @get(operation_id="ListRoles")
    async def list_roles(
        self,
        roles_service: RoleService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Role]:
        """List roles using Advanced Alchemy filters.

        Returns:
            Paginated list of role records.
        """
        roles, total = await roles_service.get_many_and_count(*filters)
        return roles_service.to_schema(roles, total, filters=filters, schema_type=Role)

    @get(operation_id="GetRole", path="/{role_id:uuid}")
    async def get_role(
        self,
        roles_service: RoleService,
        role_id: Annotated[UUID, Parameter(title="Role ID", description="The role to retrieve.")],
    ) -> Role:
        """Retrieve a role by UUID.

        Returns:
            Serialized role record.
        """
        role = await roles_service.get(role_id)
        return roles_service.to_schema(role, schema_type=Role)

    @post(operation_id="CreateRole", path="")
    async def create_role(self, roles_service: RoleService, data: RoleCreate) -> Role:
        """Create a new role.

        Returns:
            Newly created role record.
        """
        role = await roles_service.create(data.to_dict(), auto_commit=True)
        return roles_service.to_schema(role, schema_type=Role)

    @patch(operation_id="UpdateRole", path="/{role_id:uuid}")
    async def update_role(
        self,
        roles_service: RoleService,
        data: RoleUpdate,
        role_id: Annotated[UUID, Parameter(title="Role ID", description="The role to update.")],
    ) -> Role:
        """Update a non-default role.

        Returns:
            Updated role record.

        Raises:
            HTTPException: If attempting to modify or rename a protected default role.
        """
        role = await roles_service.get(role_id)
        if role.name in _PROTECTED_ROLES or data.name in _PROTECTED_ROLES:
            raise HTTPException(status_code=400, detail="Cannot update default roles")
        role = await roles_service.update(item_id=role_id, data=data.to_dict(), auto_commit=True)
        return roles_service.to_schema(role, schema_type=Role)

    @delete(operation_id="DeleteRole", path="/{role_id:uuid}")
    async def delete_role(
        self,
        roles_service: RoleService,
        role_id: Annotated[UUID, Parameter(title="Role ID", description="The role to delete.")],
    ) -> None:
        """Delete a non-default role.

        Raises:
            HTTPException: If attempting to delete a protected default role.
        """
        role = await roles_service.get(role_id)
        if role.name in _PROTECTED_ROLES:
            raise HTTPException(status_code=400, detail="Cannot delete default roles")
        _ = await roles_service.delete(role_id, auto_commit=True)

    @post(operation_id="AssignRole", path="/{role_slug:str}/assign")
    async def assign_role(
        self,
        account_services: AccountServices,
        current_user: CurrentUser[m.User],
        data: UserRoleAdd,
        role_slug: Annotated[str, Parameter(title="Role Slug", description="The role slug to assign.")],
    ) -> Message:
        """Atomically assign a role to a user and record an audit log entry.

        An unknown role or user, or a role the user already holds, surfaces as the ``HTTPException`` raised
        by ``AccountServices.assign_role``.

        Returns:
            Confirmation message for the role assignment.
        """
        await account_services.assign_role(role_slug, email=data.user_name, actor=current_user)
        return Message(message=f"Successfully assigned the '{role_slug}' role to {data.user_name}.")

    @post(operation_id="RevokeRole", path="/{role_slug:str}/revoke")
    async def revoke_role(
        self,
        account_services: AccountServices,
        current_user: CurrentUser[m.User],
        data: UserRoleRevoke,
        role_slug: Annotated[str, Parameter(title="Role Slug", description="The role slug to revoke.")],
    ) -> Message:
        """Atomically revoke a role from a user and record an audit log entry.

        An unknown role or user, or a role the user does not hold, surfaces as the ``HTTPException`` raised
        by ``AccountServices.revoke_role``.

        Returns:
            Confirmation message for the role revocation.
        """
        await account_services.revoke_role(role_slug, email=data.user_name, actor=current_user)
        return Message(message=f"Successfully revoked the '{role_slug}' role from {data.user_name}.")
