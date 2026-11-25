"""Role-related schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

import msgspec

from app.lib.schema import CamelizedBaseStruct


class UserRoleAdd(CamelizedBaseStruct):
    """Payload identifying a user by email for role assignment."""

    user_name: str


class UserRoleRevoke(CamelizedBaseStruct):
    """Payload identifying a user by email for role revocation."""

    user_name: str


class Role(CamelizedBaseStruct):
    """Serialized role response payload."""

    id: UUID
    slug: str
    name: str
    created_at: datetime
    updated_at: datetime


class RoleCreate(CamelizedBaseStruct):
    """Request payload for creating a role."""

    name: str


class RoleUpdate(CamelizedBaseStruct, omit_defaults=True):
    """Request payload for updating a role."""

    name: str | msgspec.UnsetType | None = msgspec.UNSET
