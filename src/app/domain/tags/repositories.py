from __future__ import annotations

from app.db.models import Tag
from app.lib.repository import SQLAlchemyAsyncRepository

__all__ = ("TagRepository",)


class TagRepository(SQLAlchemyAsyncRepository[Tag]):
    """Tag Repository."""

    model_type = Tag
