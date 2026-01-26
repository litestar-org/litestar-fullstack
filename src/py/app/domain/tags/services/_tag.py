from __future__ import annotations

from advanced_alchemy import repository, service

from app.db import models as m
from app.lib.service import AutoSlugServiceMixin


class TagService(AutoSlugServiceMixin[m.Tag], service.SQLAlchemyAsyncRepositoryService[m.Tag]):
    """Handles basic lookup operations for an Tag."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Tag]):
        """Tag Repository."""

        model_type = m.Tag

    repository_type = Repo
    match_fields = ["name"]
