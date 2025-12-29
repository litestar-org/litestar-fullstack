"""Admin Users Controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from litestar import Controller, delete, get, patch
from litestar.di import Provide
from litestar.params import Dependency
from sqlalchemy.orm import joinedload, load_only, selectinload, undefer_group

from app.db import models as m
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.services import UserService
from app.domain.admin.deps import provide_audit_log_service
from app.domain.admin.schemas import AdminUserDetail, AdminUserSummary, AdminUserUpdate
from app.lib.schema import Message
from app.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from litestar import Request
    from litestar.security.jwt import Token

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination

    from app.domain.accounts.services import UserService
    from app.domain.admin.services import AuditLogService


class AdminUsersController(Controller):
    """Admin user management endpoints."""

    tags = ["Admin"]
    path = "/api/admin/users"
    guards = [requires_superuser]
    dependencies = create_service_dependencies(
        UserService,
        key="users_service",
        load=[
            selectinload(m.User.roles).options(joinedload(m.UserRole.role, innerjoin=True)),
            selectinload(m.User.oauth_accounts),
            selectinload(m.User.teams).options(
                joinedload(m.TeamMember.team, innerjoin=True).options(load_only(m.Team.name)),
            ),
        ],
        uniquify=True,
        error_messages={"duplicate_key": "This user already exists.", "integrity": "User operation failed."},
        filters={
            "id_filter": UUID,
            "search": "name,email",
            "pagination_type": "limit_offset",
            "pagination_size": 25,
            "created_at": True,
            "updated_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    ) | {
        "audit_service": Provide(provide_audit_log_service),
    }

    @get(operation_id="AdminListUsers", path="/")
    async def list_users(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[AdminUserSummary]:
        """List all users with pagination.

        Args:
            request: Request with authenticated superuser
            users_service: User service
            filters: Filter and pagination parameters

        Returns:
            Paginated user list
        """
        results, total = await users_service.list_and_count(*filters)
        return users_service.to_schema(
            data=results,
            total=total,
            filters=filters,
            schema_type=AdminUserSummary,
        )

    @get(operation_id="AdminGetUser", path="/{user_id:uuid}")
    async def get_user(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        user_id: UUID,
    ) -> AdminUserDetail:
        """Get detailed user information.

        Args:
            request: Request with authenticated superuser
            users_service: User service
            user_id: ID of user to retrieve

        Returns:
            Detailed user information
        """
        user = await users_service.get(user_id, load=[undefer_group("security_sensitive")])

        return AdminUserDetail(
            id=user.id,
            email=user.email,
            name=user.name,
            username=user.username,
            phone=user.phone,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
            verified_at=user.verified_at,
            joined_at=user.joined_at,
            login_count=user.login_count,
            is_two_factor_enabled=user.is_two_factor_enabled,
            has_password=user.hashed_password is not None,
            roles=[r.role.name for r in user.roles if r.role] if user.roles else [],
            teams=[t.team.name for t in user.teams if t.team] if user.teams else [],
            oauth_providers=[a.oauth_name for a in user.oauth_accounts] if user.oauth_accounts else [],
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @patch(operation_id="AdminUpdateUser", path="/{user_id:uuid}")
    async def update_user(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        audit_service: AuditLogService,
        user_id: UUID,
        data: AdminUserUpdate,
    ) -> AdminUserDetail:
        """Update user as admin.

        Args:
            request: Request with authenticated superuser
            users_service: User service
            audit_service: Audit log service
            user_id: ID of user to update
            data: Update payload

        Returns:
            Updated user details
        """
        import msgspec

        update_data: dict[str, Any] = {}
        for field in ("name", "username", "phone", "is_active", "is_superuser", "is_verified"):
            value = getattr(data, field)
            if value is not msgspec.UNSET:
                update_data[field] = value

        user = await users_service.update(item_id=user_id, data=update_data, auto_commit=True)

        await audit_service.log_action(
            action="admin.user.update",
            actor_id=request.user.id,
            actor_email=request.user.email,
            target_type="user",
            target_id=str(user_id),
            target_label=user.email,
            details={"changes": list(update_data.keys())},
            request=request,
        )

        return AdminUserDetail(
            id=user.id,
            email=user.email,
            name=user.name,
            username=user.username,
            phone=user.phone,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
            verified_at=user.verified_at,
            joined_at=user.joined_at,
            login_count=user.login_count,
            is_two_factor_enabled=user.is_two_factor_enabled,
            has_password=user.hashed_password is not None,
            roles=[r.role.name for r in user.roles if r.role] if user.roles else [],
            teams=[t.team.name for t in user.teams if t.team] if user.teams else [],
            oauth_providers=[a.oauth_name for a in user.oauth_accounts] if user.oauth_accounts else [],
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @delete(operation_id="AdminDeleteUser", path="/{user_id:uuid}", status_code=200)
    async def delete_user(
        self,
        request: Request[m.User, Token, Any],
        users_service: UserService,
        audit_service: AuditLogService,
        user_id: UUID,
    ) -> Message:
        """Delete a user (admin only).

        Args:
            request: Request with authenticated superuser
            users_service: User service
            audit_service: Audit log service
            user_id: ID of user to delete

        Returns:
            Success message

        Raises:
            NotAuthorizedException: If attempting to delete the current user
        """
        user = await users_service.get(user_id)

        if user.id == request.user.id:
            from litestar.exceptions import NotAuthorizedException

            raise NotAuthorizedException(detail="Cannot delete your own account")

        user_email = user.email
        await users_service.delete(user_id)

        await audit_service.log_action(
            action="admin.user.delete",
            actor_id=request.user.id,
            actor_email=request.user.email,
            target_type="user",
            target_id=str(user_id),
            target_label=user_email,
            request=request,
        )

        return Message(message=f"User {user_email} deleted successfully")
