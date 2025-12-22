"""Tags domain schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas.base import CamelizedBaseStruct

if TYPE_CHECKING:
    from uuid import UUID

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
