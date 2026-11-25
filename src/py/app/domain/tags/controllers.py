"""Tag SecureController."""

from collections.abc import Collection
from typing import Annotated, ClassVar
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import (
    FilterConfig,
    create_filter_dependencies,
    create_service_provider,
)
from advanced_alchemy.filters import FilterSet, FilterTypes
from advanced_alchemy.service.pagination import OffsetPagination
from litestar import delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar_security import (
    AuthenticationPolicy,
    CurrentUser,
    SecureController,
    any_of,
    required,
    requires_role,
)
from sqlalchemy.orm import selectinload

from app.db import models as m
from app.domain.tags.schemas import Tag, TagCreate, TagUpdate
from app.domain.tags.services import TagService


class TagFilterSet(FilterSet[m.Tag]):
    """Typed filter set for querying workspace tags."""

    model_type: ClassVar[type[m.Tag]] = m.Tag
    search_fields: ClassVar[Collection[str]] = ("name", "slug")
    sort_fields: ClassVar[Collection[str]] = ("name", "slug", "created_at", "updated_at")
    config: ClassVar[FilterConfig] = {
        "id_filter": UUID,
        "pagination_type": "limit_offset",
        "pagination_size": 20,
        "created_at": True,
        "updated_at": True,
        "sort_field": "name",
        "sort_order": "asc",
    }


provide_tags_service = create_service_provider(
    TagService,
    load=[selectinload(m.Tag.teams)],
    error_messages={"duplicate_key": "This tag already exists.", "integrity": "Tag operation failed."},
)


class TagController(SecureController):
    """Handles workspace tag catalog reads, authenticated creation, and superuser administration."""

    path = "/api/tags"
    tags = ["Tags"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    dependencies = {
        "tags_service": Provide(provide_tags_service),
    } | create_filter_dependencies(TagFilterSet)

    @get(
        operation_id="ListTags",
        path="",
        opt={"auth": any_of("session", "api-key")},
        mcp_resource="tags_catalog",
    )
    async def list_tags(
        self,
        tags_service: TagService,
        current_user: CurrentUser[m.User],
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Tag]:
        """List tags in the workspace catalog.

        Returns:
            Paginated workspace tags.
        """
        _ = current_user
        results, total = await tags_service.get_many_and_count(*filters)
        return tags_service.to_schema(results, total, filters, schema_type=Tag)

    @get(operation_id="GetTag", path="/{tag_id:uuid}")
    async def get_tag(
        self,
        tags_service: TagService,
        current_user: CurrentUser[m.User],
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to retrieve.")],
    ) -> Tag:
        """Get a tag by ID.

        Returns:
            The matching tag.
        """
        _ = current_user
        db_obj = await tags_service.get(tag_id)
        return tags_service.to_schema(db_obj, schema_type=Tag)

    @post(
        operation_id="CreateTag",
        path="",
        opt={"auth": any_of("session", "api-key")},
        mcp_tool="create_tag",
        mcp_description="Create a new tag in the workspace catalog.",
    )
    async def create_tag(
        self,
        tags_service: TagService,
        current_user: CurrentUser[m.User],
        data: TagCreate,
    ) -> Tag:
        """Create a new tag in the workspace catalog.

        Returns:
            The created tag.
        """
        _ = current_user
        db_obj = await tags_service.create(data.to_dict(), auto_commit=True)
        return tags_service.to_schema(db_obj, schema_type=Tag)

    @patch(
        operation_id="UpdateTag",
        path="/{tag_id:uuid}",
        guards=[requires_role("superuser")],
    )
    async def update_tag(
        self,
        tags_service: TagService,
        data: TagUpdate,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to update.")],
    ) -> Tag:
        """Update a tag.

        Returns:
            The updated tag.
        """
        db_obj = await tags_service.update(item_id=tag_id, data=data.to_dict(), auto_commit=True)
        return tags_service.to_schema(db_obj, schema_type=Tag)

    @delete(
        operation_id="DeleteTag",
        path="/{tag_id:uuid}",
        guards=[requires_role("superuser")],
        return_dto=None,
    )
    async def delete_tag(
        self,
        tags_service: TagService,
        tag_id: Annotated[UUID, Parameter(title="Tag ID", description="The tag to delete.")],
    ) -> None:
        """Delete a tag."""
        _ = await tags_service.delete(tag_id, auto_commit=True)
