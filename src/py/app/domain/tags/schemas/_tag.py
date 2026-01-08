"""Tag schemas."""

from uuid import UUID

from app.lib.schema import CamelizedBaseStruct


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
