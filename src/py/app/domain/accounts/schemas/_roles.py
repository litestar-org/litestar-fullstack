"""Role-related schemas."""

from datetime import datetime
from uuid import UUID

import msgspec

from app.lib.schema import CamelizedBaseStruct


class UserRoleAdd(CamelizedBaseStruct):
    """User role add ."""

    user_name: str


class UserRoleRevoke(CamelizedBaseStruct):
    """User role revoke ."""

    user_name: str


class Role(CamelizedBaseStruct):
    """Holds role details for a user.

    This is nested in the User Model for 'roles'
    """

    id: UUID
    slug: str
    name: str
    created_at: datetime
    updated_at: datetime


class RoleCreate(CamelizedBaseStruct):
    name: str


class RoleUpdate(CamelizedBaseStruct):
    name: str | msgspec.UnsetType | None = msgspec.UNSET
