from __future__ import annotations

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db.models import Tag

from .repositories import TagRepository

__all__ = ("TagService",)


class TagService(SQLAlchemyAsyncRepositoryService[Tag]):
    """Handles basic lookup operations for an Tag."""

    repository_type = TagRepository
    match_fields = ["name"]
