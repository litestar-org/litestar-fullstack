from __future__ import annotations

from advanced_alchemy.extensions.litestar.repository import SQLAlchemyAsyncRepository

from app.db.models import Tag

__all__ = ("TagRepository",)


class TagRepository(SQLAlchemyAsyncRepository[Tag]):
    """Tag Repository."""

    model_type = Tag
