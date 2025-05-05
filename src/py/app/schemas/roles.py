from datetime import datetime
from uuid import UUID

import msgspec

from app.schemas.base import CamelizedBaseStruct

__all__ = (
    "Role",
    "RoleCreate",
    "RoleUpdate",
)


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
