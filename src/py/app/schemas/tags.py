# Standard Library

from uuid import UUID

from app.schemas.base import CamelizedBaseStruct


# Properties to receive via API on creation
class Tag(CamelizedBaseStruct):
    """Tag Information."""

    id: UUID
    slug: str
    name: str


class TagCreate(CamelizedBaseStruct):
    """Tag Create Properties."""

    name: str


class TagUpdate(CamelizedBaseStruct):
    """Tag Update Properties."""

    name: str | None = None
