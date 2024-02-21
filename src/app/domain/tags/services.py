from __future__ import annotations

from app.db.models import Tag
from app.lib.service import SQLAlchemyAsyncRepositoryService

from .repositories import TagRepository

__all__ = ("TagService",)


class TagService(SQLAlchemyAsyncRepositoryService[Tag]):
    """Handles basic lookup operations for an Tag."""

    repository_type = TagRepository
    match_fields = ["name"]
