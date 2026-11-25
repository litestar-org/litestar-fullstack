"""Role administration SecureController."""

from datetime import UTC, datetime
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
        results, total = await roles_service.get_many_and_count(*filters)
        return roles_service.to_schema(results, total, filters=filters, schema_type=Role)

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
        db_obj = await roles_service.get(role_id)
        return roles_service.to_schema(db_obj, schema_type=Role)

    @post(operation_id="CreateRole", path="")
    async def create_role(self, roles_service: RoleService, data: RoleCreate) -> Role:
        """Create a new role.

        Returns:
            Newly created role record.
        """
        db_obj = await roles_service.create(data.to_dict(), auto_commit=True)
        return roles_service.to_schema(db_obj, schema_type=Role)

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
        existing = await roles_service.get(role_id)
        if existing.name in _PROTECTED_ROLES or data.name in _PROTECTED_ROLES:
            raise HTTPException(status_code=400, detail="Cannot update default roles")
        db_obj = await roles_service.update(item_id=role_id, data=data.to_dict(), auto_commit=True)
        return roles_service.to_schema(db_obj, schema_type=Role)

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
        db_obj = await roles_service.get(role_id)
        if db_obj.name in _PROTECTED_ROLES:
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

        Returns:
            Confirmation message for the role assignment.

        Raises:
            HTTPException: If the role or user is not found, or the user already holds the role.
        """
        role = await account_services.roles.get_one_or_none(slug=role_slug)
        if role is None:
            raise HTTPException(status_code=404, detail=f"Role '{role_slug}' not found")
        user = await account_services.users.get_one_or_none(email=data.user_name)
        if user is None:
            raise HTTPException(status_code=404, detail=f"User '{data.user_name}' not found")
        existing = await account_services.user_roles.get_one_or_none(user_id=user.id, role_id=role.id)
        if existing is not None:
            raise HTTPException(status_code=409, detail=f"User '{data.user_name}' already has role '{role_slug}'")

        await account_services.user_roles.create(
            data={"user_id": user.id, "role_id": role.id, "assigned_at": datetime.now(UTC)},
        )
        await account_services.audit_logs.log_action(
            action="role.assigned",
            actor_id=current_user.id,
            actor_email=current_user.email,
            target_type="user",
            target_id=str(user.id),
            target_label=user.email,
            details={"role_slug": role_slug},
        )
        await account_services.session.commit()
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

        Returns:
            Confirmation message for the role revocation.

        Raises:
            HTTPException: If the role, user, or role assignment does not exist.
        """
        role = await account_services.roles.get_one_or_none(slug=role_slug)
        if role is None:
            raise HTTPException(status_code=404, detail=f"Role '{role_slug}' not found")
        user = await account_services.users.get_one_or_none(email=data.user_name)
        if user is None:
            raise HTTPException(status_code=404, detail=f"User '{data.user_name}' not found")
        existing = await account_services.user_roles.get_one_or_none(user_id=user.id, role_id=role.id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"User '{data.user_name}' does not have role '{role_slug}'")

        await account_services.user_roles.delete(existing.id)
        await account_services.audit_logs.log_action(
            action="role.revoked",
            actor_id=current_user.id,
            actor_email=current_user.email,
            target_type="user",
            target_id=str(user.id),
            target_label=user.email,
            details={"role_slug": role_slug},
        )
        await account_services.session.commit()
        return Message(message=f"Successfully revoked the '{role_slug}' role from {data.user_name}.")
