"""Admin Users SecureController."""

from typing import Annotated, Any, ClassVar
from uuid import UUID

import msgspec
from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service.pagination import OffsetPagination
from litestar import Request, delete, get, patch
from litestar.di import Provide
from litestar.exceptions import PermissionDeniedException
from litestar.params import Dependency
from litestar_security import AuthenticationPolicy, CurrentUser, SecureController, required, requires_role
from sqlalchemy.orm import selectinload, undefer_group

from app.db import models as m
from app.domain.accounts.deps import UserFilterSet, create_filter_dependencies, provide_users_service
from app.domain.accounts.services import UserService
from app.domain.admin.deps import provide_audit_log_service
from app.domain.admin.schemas import AdminUserDetail, AdminUserSummary, AdminUserUpdate
from app.domain.admin.services import AuditLogService
from app.lib.schema import Message


class AdminUsersController(SecureController):
    """Superuser user account administration endpoints."""

    path = "/api/admin/users"
    tags = ["Admin"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    guards = [requires_role("superuser")]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "audit_service": Provide(provide_audit_log_service),
    } | create_filter_dependencies(UserFilterSet)

    @get(operation_id="AdminListUsers", path="/")
    async def list_users(
        self,
        users_service: UserService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[AdminUserSummary]:
        """List all users with filtering and pagination."""
        results, total = await users_service.get_many_and_count(*filters)
        return users_service.to_schema(results, total, filters, schema_type=AdminUserSummary)

    @get(operation_id="AdminGetUser", path="/{user_id:uuid}")
    async def get_user(
        self,
        users_service: UserService,
        user_id: UUID,
    ) -> AdminUserDetail:
        """Get detailed user information including password and MFA status."""
        user = await users_service.get(
            user_id,
            load=[undefer_group("security_sensitive"), selectinload(m.User.mfa_factors)],
        )
        return users_service.to_schema(user, schema_type=AdminUserDetail)

    @patch(operation_id="AdminUpdateUser", path="/{user_id:uuid}")
    async def update_user(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
        users_service: UserService,
        audit_service: AuditLogService,
        user_id: UUID,
        data: AdminUserUpdate,
    ) -> AdminUserDetail:
        """Update user flags or profile fields as an administrator."""
        update_data: dict[str, Any] = {}
        for field in ("name", "username", "phone", "is_active", "is_superuser", "is_verified"):
            value = getattr(data, field)
            if value is not msgspec.UNSET:
                update_data[field] = value

        user = await users_service.update(item_id=user_id, data=update_data, auto_commit=True)
        await audit_service.log_admin_user_update(
            actor_id=current_user.id,
            actor_email=current_user.email,
            user_id=user_id,
            user_email=user.email,
            changes=list(update_data.keys()),
            request=request,
        )
        fresh = await users_service.get(
            user_id,
            load=[undefer_group("security_sensitive"), selectinload(m.User.mfa_factors)],
        )
        return users_service.to_schema(fresh, schema_type=AdminUserDetail)

    @delete(operation_id="AdminDeleteUser", path="/{user_id:uuid}", status_code=200)
    async def delete_user(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
        users_service: UserService,
        audit_service: AuditLogService,
        user_id: UUID,
    ) -> Message:
        """Delete a user account while preventing administrator self-deletion."""
        user = await users_service.get(user_id)
        if user.id == current_user.id:
            raise PermissionDeniedException(detail="Cannot delete your own account")
        user_email = user.email
        await users_service.delete(user_id, auto_commit=True)
        await audit_service.log_admin_user_delete(
            actor_id=current_user.id,
            actor_email=current_user.email,
            user_id=user_id,
            user_email=user_email,
            request=request,
        )
        return Message(message=f"User {user_email} deleted successfully")
