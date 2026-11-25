"""Role database service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m

if TYPE_CHECKING:
    from advanced_alchemy.service import ModelDictT


class RoleService(service.SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for roles with automatic unique slug generation."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Role]):
        """Role SQLAlchemy slug repository."""

        model_type = m.Role

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[m.Role]) -> ModelDictT[m.Role]:
        """Populate a unique slug from the role name when creating a new role.

        Returns:
            Prepared role payload with a unique slug populated when omitted.
        """
        data = service.schema_dump(data)
        if service.is_dict_without_field(data, "slug") and service.is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data
