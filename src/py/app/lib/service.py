"""Service mixins and utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from advanced_alchemy.base import ModelProtocol
from advanced_alchemy.extensions.litestar import service

if TYPE_CHECKING:
    from advanced_alchemy.repository import SQLAlchemyAsyncSlugRepository


T = TypeVar("T", bound=ModelProtocol)


class AutoSlugServiceMixin(Generic[T]):
    """Mixin to automatically populate slug field from name."""

    async def to_model_on_create(self, data: service.ModelDictT[T]) -> service.ModelDictT[T]:
        data = service.schema_dump(data)

        return await self._populate_slug(data)

    async def to_model_on_update(self, data: service.ModelDictT[T]) -> service.ModelDictT[T]:
        data = service.schema_dump(data)

        return await self._populate_slug(data)

    async def to_model_on_upsert(self, data: service.ModelDictT[T]) -> service.ModelDictT[T]:
        data = service.schema_dump(data)

        return await self._populate_slug(data)

    async def _populate_slug(self, data: service.ModelDictT[T]) -> service.ModelDictT[T]:
        if service.is_dict_without_field(data, "slug") and (name := data.get("name")) is not None:
            # We assume the service has a repository that supports slug generation

            # casting to Any to avoid circular dependency/protocol issues with 'repository' attribute

            repo = cast("SQLAlchemyAsyncSlugRepository[T]", cast("Any", self).repository)
            data["slug"] = await repo.get_available_slug(name)
        return data
