"""Role Controllers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.exceptions import HTTPException
from litestar.params import Dependency, Parameter

from app.db import models as m
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.schemas import Message, Role, RoleCreate, RoleUpdate, UserRoleAdd, UserRoleRevoke
from app.domain.accounts.services import RoleService, UserRoleService, UserService
from app.lib.constants import DEFAULT_ACCESS_ROLE, SUPERUSER_ACCESS_ROLE
from app.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination


class RoleController(Controller):
    """Handles the interactions within the Role objects."""

    path = "/api/roles"
    tags = ["Roles"]
    guards = [requires_superuser]
    dependencies = {
        **create_service_dependencies(
            RoleService,
            key="roles_service",
            load=[m.Role.users],
            filters={
                "id_filter": UUID,
                "pagination_type": "limit_offset",
                "pagination_size": 50,
                "sort_field": "name",
                "search": "name,slug",
            },
        ),
        **create_service_dependencies(UserService, key="users_service"),
        **create_service_dependencies(UserRoleService, key="user_roles_service"),
    }

    @get(operation_id="ListRoles")
    async def list_roles(
        self,
        roles_service: RoleService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Role]:
        """List roles.

        Args:
            filters: The filters to apply to the list of roles.
            roles_service: The role service.

        Returns:
            The list of roles.
        """
        results, total = await roles_service.list_and_count(*filters)
        return roles_service.to_schema(data=results, total=total, filters=filters, schema_type=Role)

    @get(operation_id="GetRole", path="/{role_id:uuid}")
    async def get_role(
        self,
        roles_service: RoleService,
        role_id: Annotated[UUID, Parameter(title="Role ID", description="The role to retrieve.")],
    ) -> Role:
        """Get a role.

        Args:
            role_id: The ID of the role to retrieve.
            roles_service: The role service.

        Returns:
            The role.
        """
        db_obj = await roles_service.get(role_id)
        return roles_service.to_schema(db_obj, schema_type=Role)

    @post(operation_id="CreateRole", path="")
    async def create_role(self, roles_service: RoleService, data: RoleCreate) -> Role:
        """Create a new role.

        Args:
            data: The data to create the role with.
            roles_service: The role service.

        Returns:
            The created role.
        """
        db_obj = await roles_service.create(data.to_dict())
        return roles_service.to_schema(db_obj, schema_type=Role)

    @patch(operation_id="UpdateRole", path="/{role_id:uuid}")
    async def update_role(
        self,
        roles_service: RoleService,
        data: RoleUpdate,
        role_id: Annotated[UUID, Parameter(title="Role ID", description="The role to update.")],
    ) -> Role:
        """Update a role.

        Args:
            data: The data to update the role with.
            role_id: The ID of the role to update.
            roles_service: The role service.

        Raises:
            HTTPException: If the role is a default role.

        Returns:
            The updated role.
        """
        if data.name in {DEFAULT_ACCESS_ROLE, SUPERUSER_ACCESS_ROLE}:
            raise HTTPException(status_code=400, detail="Cannot update default roles")
        db_obj = await roles_service.update(item_id=role_id, data=data.to_dict())
        return roles_service.to_schema(db_obj, schema_type=Role)

    @delete(operation_id="DeleteRole", path="/{role_id:uuid}")
    async def delete_role(
        self,
        roles_service: RoleService,
        role_id: Annotated[UUID, Parameter(title="Role ID", description="The role to delete.")],
    ) -> None:
        """Delete a role.

        Args:
            role_id: The ID of the role to delete.
            roles_service: The role service.

        Raises:
            HTTPException: If the role is a default role.
        """
        db_obj = await roles_service.get(role_id)
        if db_obj.name in {DEFAULT_ACCESS_ROLE, SUPERUSER_ACCESS_ROLE}:
            raise HTTPException(status_code=400, detail="Cannot delete default roles")
        _ = await roles_service.delete(role_id)

    @post(operation_id="AssignRole", path="/{role_slug:str}/assign")
    async def assign_role(
        self,
        roles_service: RoleService,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: UserRoleAdd,
        role_slug: Annotated[str, Parameter(title="Role Slug", description="The role slug to assign.")],
    ) -> Message:
        """Assign a role to a user.

        Args:
            roles_service: The role service.
            users_service: The user service.
            user_roles_service: The user role service.
            data: The user to assign the role to.
            role_slug: The slug of the role to assign.

        Returns:
            A message confirming the assignment.

        Raises:
            HTTPException: If the role or user is not found, or if the user already has the role.
        """
        role = await roles_service.get_one_or_none(slug=role_slug)
        if role is None:
            raise HTTPException(status_code=404, detail=f"Role '{role_slug}' not found")

        user = await users_service.get_one_or_none(email=data.user_name)
        if user is None:
            raise HTTPException(status_code=404, detail=f"User '{data.user_name}' not found")

        existing_role = await user_roles_service.get_one_or_none(user_id=user.id, role_id=role.id)
        if existing_role is not None:
            raise HTTPException(status_code=409, detail=f"User '{data.user_name}' already has role '{role_slug}'")

        await user_roles_service.create(
            data={
                "user_id": user.id,
                "role_id": role.id,
                "assigned_at": datetime.now(UTC),
            },
        )

        return Message(message=f"Successfully assigned the '{role_slug}' role to {data.user_name}.")

    @post(operation_id="RevokeRole", path="/{role_slug:str}/revoke")
    async def revoke_role(
        self,
        roles_service: RoleService,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: UserRoleRevoke,
        role_slug: Annotated[str, Parameter(title="Role Slug", description="The role slug to revoke.")],
    ) -> Message:
        """Revoke a role from a user.

        Args:
            roles_service: The role service.
            users_service: The user service.
            user_roles_service: The user role service.
            data: The user to revoke the role from.
            role_slug: The slug of the role to revoke.

        Returns:
            A message confirming the revocation.

        Raises:
            HTTPException: If the role or user is not found, or if the user doesn't have the role.
        """
        role = await roles_service.get_one_or_none(slug=role_slug)
        if role is None:
            raise HTTPException(status_code=404, detail=f"Role '{role_slug}' not found")

        user = await users_service.get_one_or_none(email=data.user_name)
        if user is None:
            raise HTTPException(status_code=404, detail=f"User '{data.user_name}' not found")

        existing_role = await user_roles_service.get_one_or_none(user_id=user.id, role_id=role.id)
        if existing_role is None:
            raise HTTPException(status_code=404, detail=f"User '{data.user_name}' does not have role '{role_slug}'")

        await user_roles_service.delete(existing_role.id)

        return Message(message=f"Successfully revoked the '{role_slug}' role from {data.user_name}.")
