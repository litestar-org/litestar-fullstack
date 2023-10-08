from __future__ import annotations

from app.domain.tags.models import Tag
from app.lib.repository import SQLAlchemyAsyncRepository
from app.lib.service import SQLAlchemyAsyncRepositoryService

__all__ = ["TagService", "TagRepository"]


class TagRepository(SQLAlchemyAsyncRepository[Tag]):
    """Tag Repository."""

    model_type = Tag


class TagService(SQLAlchemyAsyncRepositoryService[Tag]):
    """Handles basic lookup operations for an Tag."""

    repository_type = TagRepository
    match_fields = ["name"]
