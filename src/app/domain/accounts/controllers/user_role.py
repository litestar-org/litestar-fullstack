"""User Routes."""

from __future__ import annotations

from litestar import Controller, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.repository.exceptions import ConflictError

from app.domain.accounts import deps, schemas, urls
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.services import RoleService, UserRoleService, UserService
from app.lib.deps import create_service_provider
from app.lib.schema import Message


class UserRoleController(Controller):
    """Handles the adding and removing of User Role records."""

    tags = ["User Account Roles"]
    guards = [requires_superuser]
    dependencies = {
        "user_roles_service": Provide(create_service_provider(UserRoleService)),
        "roles_service": Provide(create_service_provider(RoleService)),
        "users_service": Provide(deps.provide_users_service),
    }

    @post(operation_id="AssignUserRole", path=urls.ACCOUNT_ASSIGN_ROLE)
    async def assign_role(
        self,
        roles_service: RoleService,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: schemas.UserRoleAdd,
        role_slug: str = Parameter(title="Role Slug", description="The role to grant."),
    ) -> Message:
        """Create a new migration role."""
        role_id = (await roles_service.get_one(slug=role_slug)).id
        user_obj = await users_service.get_one(email=data.user_name)
        obj, created = await user_roles_service.get_or_upsert(role_id=role_id, user_id=user_obj.id)
        if created:
            return Message(message=f"Successfully assigned the '{obj.role_slug}' role to {obj.user_email}.")
        return Message(message=f"User {obj.user_email} already has the '{obj.role_slug}' role.")

    @post(operation_id="RevokeUserRole", path=urls.ACCOUNT_REVOKE_ROLE)
    async def revoke_role(
        self,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: schemas.UserRoleRevoke,
        role_slug: str = Parameter(title="Role Slug", description="The role to revoke."),
    ) -> Message:
        """Delete a role from the system."""
        user_obj = await users_service.get_one(email=data.user_name)
        removed_role: bool = False
        for user_role in user_obj.roles:
            if user_role.role_slug == role_slug:
                _ = await user_roles_service.delete(user_role.id)
                removed_role = True
        if not removed_role:
            msg = "User did not have role assigned."
            raise ConflictError(msg)
        return Message(message=f"Removed the '{role_slug}' role from User {user_obj.email}.")
