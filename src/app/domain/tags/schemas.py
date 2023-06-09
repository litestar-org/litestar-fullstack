from uuid import UUID

from app.lib.schema import CamelizedBaseModel

__all__ = ["Tag", "TagCreate", "TagUpdate"]


# Properties to receive via API on creation
class Tag(CamelizedBaseModel):
    """Tag Information."""

    id: UUID
    name: str


class TagCreate(CamelizedBaseModel):
    """Tag Create Properties."""

    name: str


class TagUpdate(CamelizedBaseModel):
    """Tag Update Properties."""

    name: str | None = None
