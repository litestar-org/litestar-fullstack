from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db import models as m

__all__ = ("TagService",)


class TagService(SQLAlchemyAsyncRepositoryService[m.Tag]):
    """Handles basic lookup operations for an Tag."""

    class Repository(SQLAlchemyAsyncRepository[m.Tag]):
        """Tag Repository."""

        model_type = m.Tag

    repository_type = Repository
    match_fields = ["name"]
