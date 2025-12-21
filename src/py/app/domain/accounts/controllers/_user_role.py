"""User Role Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from advanced_alchemy.exceptions import IntegrityError
from litestar import Controller, delete, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.status_codes import HTTP_202_ACCEPTED

from app.domain.accounts.dependencies import provide_roles_service, provide_user_roles_service, provide_users_service
from app.schemas.base import Message

if TYPE_CHECKING:
    from app.domain.accounts.schemas import UserRoleAdd, UserRoleRevoke
    from app.domain.accounts.services import RoleService, UserRoleService, UserService


class UserRoleController(Controller):
    """Handles the adding and removing of User Role records."""

    path = "/api/users/roles"
    tags = ["User Account Roles"]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "roles_service": Provide(provide_roles_service),
        "user_roles_service": Provide(provide_user_roles_service),
    }

    @post(operation_id="AssignUserRole")
    async def assign_role(
        self,
        roles_service: RoleService,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: UserRoleAdd,
        role_slug: str = Parameter(title="Role Slug", description="The role to grant."),
    ) -> Message:
        """Create a new migration role.

        Args:
            roles_service: Role Service
            users_service: User Service
            user_roles_service: User Role Service
            data: User Role Add
            role_slug: Role Slug

        Returns:
            Message
        """
        role_id = (await roles_service.get_one(slug=role_slug)).id
        user_obj = await users_service.get_one(email=data.user_name)
        obj, created = await user_roles_service.get_or_upsert(role_id=role_id, user_id=user_obj.id)
        if created:
            return Message(message=f"Successfully assigned the '{obj.role_slug}' role to {obj.user_email}.")
        return Message(message=f"User {obj.user_email} already has the '{obj.role_slug}' role.")

    @delete(operation_id="RevokeUserRole", status_code=HTTP_202_ACCEPTED)
    async def revoke_role(
        self,
        users_service: UserService,
        user_roles_service: UserRoleService,
        data: UserRoleRevoke,
        role_slug: Annotated[str, Parameter(title="Role Slug", description="The role to revoke.")],
    ) -> Message:
        """Delete a role from the system.

        Args:
            users_service: User Service
            user_roles_service: User Role Service
            data: User Role Revoke
            role_slug: Role Slug

        Raises:
            IntegrityError: If the user does not have the role assigned.

        Returns:
            Message
        """
        user_obj = await users_service.get_one(email=data.user_name)
        removed_role: bool = False
        for user_role in user_obj.roles:
            if user_role.role_slug == role_slug:
                _ = await user_roles_service.delete(user_role.id)
                removed_role = True
        if not removed_role:
            msg = "User did not have role assigned."
            raise IntegrityError(msg)
        return Message(message=f"Removed the '{role_slug}' role from User {user_obj.email}.")
