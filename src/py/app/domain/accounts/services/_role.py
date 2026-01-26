from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m
from app.lib.service import AutoSlugServiceMixin


class RoleService(AutoSlugServiceMixin[m.Role], service.SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for users."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Role]):
        """User SQLAlchemy Repository."""

        model_type = m.Role

    repository_type = Repo
    match_fields = ["name"]
