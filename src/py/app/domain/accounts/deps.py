"""Account domain Advanced Alchemy service and filter providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import (
    FilterConfig,
    create_filter_dependencies,
    create_service_provider,
)
from advanced_alchemy.filters import FilterSet
from sqlalchemy.orm import joinedload, load_only, selectinload, undefer_group

from app.db import models as m
from app.domain.accounts.services import (
    AccountServices,
    RoleService,
    UserRoleService,
    UserService,
)

if TYPE_CHECKING:
    from collections.abc import Collection

USER_LOAD_OPTIONS = [
    undefer_group("security_sensitive"),
    selectinload(m.User.roles).options(joinedload(m.UserRole.role, innerjoin=True)),
    selectinload(m.User.oauth_accounts),
    selectinload(m.User.mfa_factors),
    selectinload(m.User.teams).options(
        joinedload(m.TeamMember.team, innerjoin=True).options(load_only(m.Team.name)),
    ),
]


class UserFilterSet(FilterSet[m.User]):
    """Typed filter set for querying user accounts."""

    model_type: ClassVar[type[m.User]] = m.User
    search_fields: ClassVar[Collection[str]] = ("name", "email")
    sort_fields: ClassVar[Collection[str]] = ("created_at", "updated_at", "email", "name")
    config: ClassVar[FilterConfig] = {
        "id_filter": UUID,
        "pagination_type": "limit_offset",
        "pagination_size": 25,
        "created_at": True,
        "updated_at": True,
        "sort_field": "created_at",
        "sort_order": "desc",
    }


class RoleFilterSet(FilterSet[m.Role]):
    """Typed filter set for querying roles."""

    model_type: ClassVar[type[m.Role]] = m.Role
    search_fields: ClassVar[Collection[str]] = ("name", "slug")
    sort_fields: ClassVar[Collection[str]] = ("name", "slug", "created_at", "updated_at")
    config: ClassVar[FilterConfig] = {
        "id_filter": UUID,
        "pagination_type": "limit_offset",
        "pagination_size": 50,
        "sort_field": "name",
        "sort_order": "asc",
    }


provide_users_service = create_service_provider(
    UserService,
    load=USER_LOAD_OPTIONS,
    uniquify=True,
    error_messages={"duplicate_key": "User with this email already exists.", "integrity": "User operation failed."},
)

provide_roles_service = create_service_provider(
    RoleService,
    load=[selectinload(m.Role.users)],
    error_messages={
        "duplicate_key": "This role already exists.",
        "integrity": "Role operation failed.",
    },
)

provide_user_roles_service = create_service_provider(
    UserRoleService,
    load=[
        selectinload(m.UserRole.user),
        selectinload(m.UserRole.role),
    ],
    error_messages={
        "duplicate_key": "User already has this role.",
        "integrity": "User role operation failed.",
    },
)

provide_account_services = create_service_provider(
    AccountServices,
    uniquify=True,
)

__all__ = (
    "USER_LOAD_OPTIONS",
    "RoleFilterSet",
    "UserFilterSet",
    "create_filter_dependencies",
    "provide_account_services",
    "provide_roles_service",
    "provide_user_roles_service",
    "provide_users_service",
)
