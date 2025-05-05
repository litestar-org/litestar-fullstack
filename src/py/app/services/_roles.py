from __future__ import annotations

from litestar.plugins.sqlalchemy import repository, service

from app.db import models as m


class RoleService(service.SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for users."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Role]):
        """User SQLAlchemy Repository."""

        model_type = m.Role

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: service.ModelDictT[m.Role]) -> service.ModelDictT[m.Role]:
        data = service.schema_dump(data)
        if service.is_dict_without_field(data, "slug"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def to_model_on_update(self, data: service.ModelDictT[m.Role]) -> service.ModelDictT[m.Role]:
        data = service.schema_dump(data)
        if service.is_dict_without_field(data, "slug") and service.is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def to_model_on_upsert(self, data: service.ModelDictT[m.Role]) -> service.ModelDictT[m.Role]:
        data = service.schema_dump(data)
        if service.is_dict_without_field(data, "slug") and (role_name := data.get("name")) is not None:
            data["slug"] = await self.repository.get_available_slug(role_name)
        return data
