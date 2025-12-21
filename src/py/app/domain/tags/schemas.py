"""Tags domain schemas."""

from __future__ import annotations

from uuid import UUID

from app.schemas.base import CamelizedBaseStruct

__all__ = (
    "Tag",
    "TagCreate",
    "TagUpdate",
)


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
