from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO
from litestar import Controller, delete, get, patch, post
from sqlalchemy.orm import selectinload

from app.db import models as m
from app.domain.accounts.guards import requires_active_user, requires_superuser
from app.domain.tags.services import TagService
from app.lib import dto
from app.lib.deps import create_service_provider

from . import urls

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination
    from litestar.dto import DTOData
    from litestar.params import Dependency, Parameter


class TagDTO(SQLAlchemyDTO[m.Tag]):
    config = dto.config(max_nested_depth=0, exclude={"created_at", "updated_at", "teams"})


class TagCreateDTO(SQLAlchemyDTO[m.Tag]):
    config = dto.config(max_nested_depth=0, exclude={"id", "created_at", "updated_at", "teams"})


class TagUpdateDTO(SQLAlchemyDTO[m.Tag]):
    config = dto.config(max_nested_depth=0, exclude={"id", "created_at", "updated_at", "teams"}, partial=True)


class TagController(Controller):
    """Handles the interactions within the Tag objects.

    We use a DTO in this controller purely as an example of how to integrate it with SQLAlchemy.

    You can use either pattern you see in this repository as an example.
    """

    guards = [requires_active_user]
    dependencies = {
        "tags_service": create_service_provider(
            TagService,
            load=[selectinload(m.Tag.teams, recursion_depth=2)],
        ),
    }
    signature_types = [TagService]
    tags = ["Tags"]
    return_dto = TagDTO

    @get(operation_id="ListTags", path=urls.TAG_LIST)
    async def list_tags(
        self,
        tags_service: TagService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[m.Tag]:
        """List tags."""
        results, total = await tags_service.list_and_count(*filters)
        return tags_service.to_schema(data=results, total=total, filters=filters)

    @get(operation_id="GetTag", path=urls.TAG_DETAILS)
    async def get_tag(
        self,
        tags_service: TagService,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to retrieve.")],
    ) -> m.Tag:
        """Get a tag."""
        db_obj = await tags_service.get(tag_id)
        return tags_service.to_schema(db_obj)

    @post(operation_id="CreateTag", guards=[requires_superuser], path=urls.TAG_CREATE, dto=TagCreateDTO)
    async def create_tag(self, tags_service: TagService, data: DTOData[m.Tag]) -> m.Tag:
        """Create a new tag."""
        db_obj = await tags_service.create(data.create_instance())
        return tags_service.to_schema(db_obj)

    @patch(operation_id="UpdateTag", path=urls.TAG_UPDATE, guards=[requires_superuser], dto=TagUpdateDTO)
    async def update_tag(
        self,
        tags_service: TagService,
        data: DTOData[m.Tag],
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to update.")],
    ) -> m.Tag:
        """Update a tag."""
        db_obj = await tags_service.update(item_id=tag_id, data=data.create_instance())
        return tags_service.to_schema(db_obj)

    @delete(operation_id="DeleteTag", path=urls.TAG_DELETE, guards=[requires_superuser], return_dto=None)
    async def delete_tag(
        self,
        tags_service: TagService,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to delete.")],
    ) -> None:
        """Delete a tag."""
        _ = await tags_service.delete(tag_id)
