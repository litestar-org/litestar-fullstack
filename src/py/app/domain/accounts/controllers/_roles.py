"""Role Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.exceptions import HTTPException
from litestar.params import Dependency, Parameter

from app.db import models as m
from app.domain.accounts.schemas import Role, RoleCreate, RoleUpdate
from app.domain.accounts.services import RoleService
from app.lib.constants import DEFAULT_ACCESS_ROLE, SUPERUSER_ACCESS_ROLE
from app.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination


class RoleController(Controller):
    """Handles the interactions within the Role objects."""

    path = "/api/roles"
    tags = ["Roles"]
    dependencies = create_service_dependencies(
        RoleService,
        key="roles_service",
        load=[m.Role.users],
        filters={
            "id_filter": UUID,
            "sort_field": "name",
            "search": "name,slug",
        },
    )

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

    @post(operation_id="CreateRole", path="/{role_id:uuid}")
    async def create_role(self, roles_service: RoleService, data: RoleCreate) -> Role:
        """Create a new role.

        Args:
            data: The data to create the role with.
            roles_service: The role service.

        Returns:
            The created role.
        """
        db_obj = await roles_service.create(data)
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
        db_obj = await roles_service.update(item_id=role_id, data=data)
        return roles_service.to_schema(db_obj, schema_type=Role)

    @delete(operation_id="DeleteRole", path="/{role_id:uuid}")
    async def delete_role(
        self,
        roles_service: RoleService,
        role_id: Annotated[UUID, Parameter(title="Role ID", description="The role to delete.")],
    ) -> None:
        """Delete a tag.

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
