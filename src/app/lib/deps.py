"""Application dependency providers."""

from __future__ import annotations

from datetime import datetime
from inspect import Parameter as InspectParameter
from inspect import Signature
from typing import TYPE_CHECKING, Any, Literal, NotRequired, TypedDict, TypeVar
from uuid import UUID

from advanced_alchemy.filters import (
    BeforeAfter,
    CollectionFilter,
    FilterTypes,
    LimitOffset,
    OrderBy,
    SearchFilter,
)
from advanced_alchemy.service import (
    Empty,
    EmptyType,
    ErrorMessages,
    LoadSpec,
    ModelT,
    SQLAlchemyAsyncRepositoryService,
)
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app.config import app as c

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from advanced_alchemy.config.asyncio import SQLAlchemyAsyncConfig
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession

DTorNone = datetime | None
StringOrNone = str | None
UuidOrNone = UUID | None
BooleanOrNone = bool | None
SortOrder = Literal["asc", "desc"]
SortOrderOrNone = Literal["asc", "desc"] | None
PaginationTypes = Literal["limit_offset"]
IdentityT = TypeVar("IdentityT", bound=UUID | int)
ServiceT_co = TypeVar("ServiceT_co", bound=SQLAlchemyAsyncRepositoryService[Any], covariant=True)

DEFAULT_IDENTITY_FIELD: str = "id"
DEFAULT_PAGINATION_SIZE: int = 20


class FilterConfig(TypedDict, total=False):
    """Configuration for filter dependencies."""

    id_filter: NotRequired[type[UUID | int]]
    id_field: NotRequired[str]
    sort_field: NotRequired[str]
    sort_order: NotRequired[SortOrder]
    pagination_type: NotRequired[PaginationTypes]
    pagination_size: NotRequired[int]
    search_fields: NotRequired[list[str] | str]
    search_is_case_sensitive: NotRequired[bool]
    created_at: NotRequired[bool]
    updated_at: NotRequired[bool]


def create_filter_dependencies(config: FilterConfig) -> Provide:  # noqa: C901
    """Create filter dependencies based on configuration.

    Args:
        config: FilterConfig instance with desired settings

    Returns:
        Dictionary of dependency overrides
    """
    providers: dict[str, Provide] = {}
    parameters: dict[str, InspectParameter] = {}

    def _provide_id_filter(
        ids: list[IdentityT] | None = Parameter(query="ids", default=None, required=False),
    ) -> CollectionFilter[IdentityT]:
        return CollectionFilter(field_name=config.get("id_field", DEFAULT_IDENTITY_FIELD), values=ids or [])

    def _provide_order_by(
        field_name: str = Parameter(title="Order by field", query="orderBy", default=config.get("sort_field", "id")),
        sort_order: SortOrder = Parameter(
            title="Sort order",
            query="sortOrder",
            default=config.get("sort_order", "desc"),
        ),
    ) -> OrderBy:
        return OrderBy(field_name=field_name, sort_order=sort_order)

    def _provide_search_filter(
        field: set[str] | str = Parameter(title="Field to search", query="searchField"),
        search: str = Parameter(title="Search string", query="searchString"),
        ignore_case: BooleanOrNone = Parameter(
            title="Search should be case sensitive",
            query="searchIgnoreCase",
            default=config.get("search_is_case_sensitive", False),
        ),
    ) -> SearchFilter:
        return SearchFilter(field_name=field, value=search, ignore_case=ignore_case or False)

    def _provide_created_filter(
        before: DTorNone = Parameter(query="createdBefore", default=None, required=False),
        after: DTorNone = Parameter(query="createdAfter", default=None, required=False),
    ) -> BeforeAfter:
        return BeforeAfter("created_at", before, after)

    def _provide_updated_filter(
        before: DTorNone = Parameter(query="updatedBefore", default=None, required=False),
        after: DTorNone = Parameter(query="updatedAfter", default=None, required=False),
    ) -> BeforeAfter:
        return BeforeAfter("updated_at", before, after)

    def _provide_limit_offset_pagination(
        current_page: int = Parameter(ge=1, query="currentPage", default=1, required=False),
        page_size: int = Parameter(
            query="pageSize",
            ge=1,
            default=config.get("pagination_size", DEFAULT_PAGINATION_SIZE),
            required=False,
        ),
    ) -> LimitOffset:
        return LimitOffset(page_size, page_size * (current_page - 1))

    def filter_aggregator(**kwargs: FilterTypes) -> list[FilterTypes]:
        """Aggregate configured filters based on their values."""
        filters: list[FilterTypes] = []

        # Handle ID filter
        id_filter = kwargs.get("id_filter")
        if id_filter and getattr(id_filter, "values", None):
            filters.append(id_filter)

        # Add standard filters
        filters.extend(
            filter_value
            for key in ["created_filter", "limit_offset", "updated_filter"]
            if (filter_value := kwargs.get(key)) is not None
        )

        # Handle search filter
        search_filter = kwargs.get("search_filter")
        if (
            search_filter
            and getattr(search_filter, "field_name", None) is not None
            and getattr(search_filter, "value", None) is not None
        ):
            filters.append(search_filter)

        # Handle order by
        order_by = kwargs.get("order_by")
        if order_by and getattr(order_by, "field_name", None) is not None:
            filters.append(order_by)

        return filters

    # Create a new signature for the function based on configured parameters
    filter_aggregator.__signature__ = Signature(  # type: ignore
        parameters=list(parameters.values()),
        return_annotation=list[FilterTypes],
    )

    # Build providers and parameters based on config
    if config.get("id_filter"):
        providers["id_filter"] = Provide(_provide_id_filter, sync_to_thread=False)
        parameters["id_filter"] = InspectParameter(
            name="id_filter",
            kind=InspectParameter.KEYWORD_ONLY,
            annotation=CollectionFilter,
            default=Dependency(skip_validation=True),
        )

    if config.get("created_at"):
        providers["created_filter"] = Provide(_provide_created_filter, sync_to_thread=False)
        parameters["created_filter"] = InspectParameter(
            name="created_filter",
            kind=InspectParameter.KEYWORD_ONLY,
            annotation=BeforeAfter,
            default=Dependency(skip_validation=True),
        )

    if config.get("updated_at"):
        providers["updated_filter"] = Provide(_provide_updated_filter, sync_to_thread=False)
        parameters["updated_filter"] = InspectParameter(
            name="updated_filter",
            kind=InspectParameter.KEYWORD_ONLY,
            annotation=BeforeAfter,
            default=Dependency(skip_validation=True),
        )

    if config.get("sort_field"):
        providers["order_by"] = Provide(_provide_order_by, sync_to_thread=False)
        parameters["order_by"] = InspectParameter(
            name="order_by",
            kind=InspectParameter.KEYWORD_ONLY,
            annotation=OrderBy,
            default=Dependency(skip_validation=True),
        )

    if config.get("search_fields"):
        providers["search_filter"] = Provide(_provide_search_filter, sync_to_thread=False)
        parameters["search_filter"] = InspectParameter(
            name="search_filter",
            kind=InspectParameter.KEYWORD_ONLY,
            annotation=SearchFilter,
            default=Dependency(skip_validation=True),
        )

    if config.get("pagination_type") == "limit_offset":
        providers["limit_offset"] = Provide(_provide_limit_offset_pagination, sync_to_thread=False)
        parameters["limit_offset"] = InspectParameter(
            name="limit_offset",
            kind=InspectParameter.KEYWORD_ONLY,
            annotation=LimitOffset,
            default=Dependency(skip_validation=True),
        )
    return Provide(filter_aggregator, sync_to_thread=False)


def create_service_provider(
    service_class: type[ServiceT_co],
    /,
    statement: Select[tuple[ModelT]] | None = None,
    config: SQLAlchemyAsyncConfig | None = c.alchemy,
    error_messages: ErrorMessages | None | EmptyType = Empty,
    load: LoadSpec | None = None,
    execution_options: dict[str, Any] | None = None,
) -> Callable[..., AsyncGenerator[ServiceT_co, None]]:
    """Create a dependency provider for a service."""

    async def provide_service(
        db_session: AsyncSession | None = None,
    ) -> AsyncGenerator[ServiceT_co, None]:
        async with service_class.new(
            session=db_session,
            statement=statement,
            config=config,
            error_messages=error_messages,
            load=load,
            execution_options=execution_options,
        ) as service:
            yield service

    return provide_service
