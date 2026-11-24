"""Tag database service with unique slug generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m

if TYPE_CHECKING:
    from advanced_alchemy.service import ModelDictT


class TagService(service.SQLAlchemyAsyncRepositoryService[m.Tag]):
    """Handles CRUD and unique slug generation for workspace tags."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Tag]):
        """Tag SQLAlchemy slug repository."""

        model_type = m.Tag

    repository_type = Repo
    match_fields = ["name"]

    async def update(self, data: ModelDictT[m.Tag], item_id: Any | None = None, **kwargs: Any) -> m.Tag:
        """Preserve the existing slug when updating a tag without changing its name."""
        if (
            item_id is not None
            and service.is_dict_with_field(data, "name")
            and service.is_dict_without_field(data, "slug")
        ):
            existing = await self.get(item_id)
            if existing.name == data["name"]:
                data["slug"] = existing.slug
        return await super().update(data, item_id=item_id, **kwargs)

    async def to_model_on_create(self, data: ModelDictT[m.Tag]) -> ModelDictT[m.Tag]:
        """Populate a unique slug from ``name`` when creating a tag."""
        return await self._populate_slug(service.schema_dump(data))

    async def to_model_on_update(self, data: ModelDictT[m.Tag]) -> ModelDictT[m.Tag]:
        """Populate a unique slug when updating a tag's name without an explicit slug."""
        return await self._populate_slug(service.schema_dump(data))

    async def to_model_on_upsert(self, data: ModelDictT[m.Tag]) -> ModelDictT[m.Tag]:
        """Populate a unique slug when upserting a tag."""
        return await self._populate_slug(service.schema_dump(data))

    async def _populate_slug(self, data: ModelDictT[m.Tag]) -> ModelDictT[m.Tag]:
        if service.is_dict_without_field(data, "slug") and service.is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(str(data["name"]))
        return data
