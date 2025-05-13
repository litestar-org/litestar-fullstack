from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from litestar import Controller, delete, get, patch, post

from app import schemas as s
from app.db import models as m
from app.lib.deps import create_service_dependencies
from app.server.security import requires_active_user, requires_superuser
from app.services import TagService

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination
    from litestar.params import Dependency, Parameter


class TagController(Controller):
    """Handles the interactions within the Tag objects."""

    path = "/api/tags"
    guards = [requires_active_user]
    dependencies = create_service_dependencies(
        TagService,
        key="tags_service",
        load=[m.Tag.teams],
        filters={
            "id_filter": UUID,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "search": "name,slug",
        },
    )
    tags = ["Tags"]

    @get(operation_id="ListTags")
    async def list_tags(
        self,
        tags_service: TagService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[s.Tag]:
        """List tags.

        Args:
            filters: The filters to apply to the list of tags.
            tags_service: The tag service.

        Returns:
            The list of tags.
        """
        results, total = await tags_service.list_and_count(*filters)
        return tags_service.to_schema(data=results, total=total, filters=filters, schema_type=s.Tag)

    @get(operation_id="GetTag", path="/{tag_id:uuid}")
    async def get_tag(
        self,
        tags_service: TagService,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to retrieve.")],
    ) -> s.Tag:
        """Get a tag.

        Args:
            tag_id: The ID of the tag to retrieve.
            tags_service: The tag service.

        Returns:
            The tag.
        """
        db_obj = await tags_service.get(tag_id)
        return tags_service.to_schema(db_obj, schema_type=s.Tag)

    @post(operation_id="CreateTag", guards=[requires_superuser], path="/{tag_id:uuid}")
    async def create_tag(self, tags_service: TagService, data: s.TagCreate) -> s.Tag:
        """Create a new tag.

        Args:
            data: The data to create the tag with.
            tags_service: The tag service.

        Returns:
            The created tag.
        """
        db_obj = await tags_service.create(data)
        return tags_service.to_schema(db_obj, schema_type=s.Tag)

    @patch(operation_id="UpdateTag", path="/{tag_id:uuid}", guards=[requires_superuser])
    async def update_tag(
        self,
        tags_service: TagService,
        data: s.TagUpdate,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to update.")],
    ) -> s.Tag:
        """Update a tag.

        Args:
            data: The data to update the tag with.
            tag_id: The ID of the tag to update.
            tags_service: The tag service.

        Returns:
            The updated tag.
        """
        db_obj = await tags_service.update(item_id=tag_id, data=data)
        return tags_service.to_schema(db_obj, schema_type=s.Tag)

    @delete(operation_id="DeleteTag", path="/{tag_id:uuid}", guards=[requires_superuser], return_dto=None)
    async def delete_tag(
        self,
        tags_service: TagService,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to delete.")],
    ) -> None:
        """Delete a tag.

        Args:
            tag_id: The ID of the tag to delete.
            tags_service: The tag service.
        """
        _ = await tags_service.delete(tag_id)
