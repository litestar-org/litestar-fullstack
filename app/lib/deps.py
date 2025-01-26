"""Application dependency providers generators.

This module contains functions to create dependency providers for services and filters.

You should not have modify this module very often and should only be invoked under normal usage.
"""

from __future__ import annotations

import datetime
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NotRequired,
    TypedDict,
    TypeVar,
    cast,
)
from uuid import UUID

from advanced_alchemy.filters import (
    BeforeAfter,
    CollectionFilter,
    FilterTypes,
    LimitOffset,
    OrderBy,
    SearchFilter,
)
from advanced_alchemy.service import Empty, EmptyType, ErrorMessages, LoadSpec, ModelT, SQLAlchemyAsyncRepositoryService
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app.config import app as c

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from advanced_alchemy.config.asyncio import SQLAlchemyAsyncConfig
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = (
    "CREATED_FILTER_DEPENDENCY_KEY",
    "DEFAULT_IDENTITY_FIELD",
    "DEFAULT_PAGINATION_SIZE",
    "FILTERS_DEPENDENCY_KEY",
    "ID_FILTER_DEPENDENCY_KEY",
    "LIMIT_OFFSET_DEPENDENCY_KEY",
    "ORDER_BY_DEPENDENCY_KEY",
    "SEARCH_FILTER_DEPENDENCY_KEY",
    "UPDATED_FILTER_DEPENDENCY_KEY",
    "BooleanOrNone",
    "DTorNone",
    "DependencyCache",
    "FilterConfig",
    "IntOrNone",
    "ServiceT_co",
    "SortOrder",
    "SortOrderOrNone",
    "StringOrNone",
    "UuidOrNone",
    "create_filter_dependencies",
    "create_service_dependencies",
    "create_service_provider",
    "dep_cache",
)

DTorNone = datetime.datetime | None
StringOrNone = str | None
UuidOrNone = UUID | None
IntOrNone = int | None
BooleanOrNone = bool | None
SortOrder = Literal["asc", "desc"]
SortOrderOrNone = SortOrder | None
ServiceT_co = TypeVar("ServiceT_co", bound=SQLAlchemyAsyncRepositoryService[Any], covariant=True)

FILTERS_DEPENDENCY_KEY = "filters"
"""Key for the filters dependency."""
CREATED_FILTER_DEPENDENCY_KEY = "created_filter"
"""Key for the created filter dependency."""
ID_FILTER_DEPENDENCY_KEY = "id_filter"
"""Key for the id filter dependency."""
LIMIT_OFFSET_DEPENDENCY_KEY = "limit_offset"
"""Key for the limit offset dependency."""
UPDATED_FILTER_DEPENDENCY_KEY = "updated_filter"
"""Key for the updated filter dependency."""
ORDER_BY_DEPENDENCY_KEY = "order_by"
"""Key for the order by dependency."""
SEARCH_FILTER_DEPENDENCY_KEY = "search_filter"
"""Key for the search filter dependency."""
DEFAULT_IDENTITY_FIELD: str = "id"
"""Default identity field on SQLAlchemy models."""
DEFAULT_PAGINATION_SIZE: int = 20
"""Default pagination size."""


class FilterConfig(TypedDict):
    """Configuration for generating dynamic filters."""

    id_filter: NotRequired[type[UUID | int]]
    """Indicates that the id filter should be enabled.  When set, the type specified will be used for the :class:`CollectionFilter`."""
    id_field: NotRequired[str]
    """The field on the model that stored the primary key or identifier."""
    sort_field: NotRequired[str]
    """The default field to use for the sort filter."""
    sort_order: NotRequired[SortOrder]
    """The default order to use for the sort filter."""
    pagination_type: NotRequired[Literal["limit_offset"]]
    """When set, pagination is enabled based on the type specified."""
    pagination_size: NotRequired[int]
    """The size of the pagination."""
    search: NotRequired[bool]
    """When set, search is enabled."""
    search_ignore_case: NotRequired[bool]
    """When set, search is case insensitive by default."""
    created_at: NotRequired[bool]
    """When set, created_at filter is enabled."""
    updated_at: NotRequired[bool]
    """When set, updated_at filter is enabled."""


class SingletonMeta(type):
    """Metaclass for singleton pattern."""

    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class DependencyCache(metaclass=SingletonMeta):
    """Simple dependency cache for the application.  This is used to help memoize dependencies that are generated dynamically."""

    def __init__(self) -> None:
        self.dependencies: dict[int | str, dict[str, Provide]] = {}

    def add_dependencies(self, key: str | int, dependencies: dict[str, Provide]) -> None:
        self.dependencies[key] = dependencies

    def get_dependencies(self, key: str | int) -> dict[str, Provide] | None:
        return self.dependencies.get(key)


dep_cache = DependencyCache()


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


def create_service_dependencies(
    service_class: type[ServiceT_co],
    /,
    key: str,
    statement: Select[tuple[ModelT]] | None = None,
    config: SQLAlchemyAsyncConfig | None = c.alchemy,
    error_messages: ErrorMessages | None | EmptyType = Empty,
    load: LoadSpec | None = None,
    execution_options: dict[str, Any] | None = None,
    filters: FilterConfig | None = None,
) -> dict[str, Provide]:
    """Create a dependency provider for the combined filter function.

    Args:
        key: The key to use for the dependency provider.
        service_class: The service class to create a dependency provider for.
        statement: The statement to use for the service.
        config: The configuration to use for the service.
        error_messages: The error messages to use for the service.
        load: The load spec to use for the service.
        execution_options: The execution options to use for the service.
        filters: The filter configuration to use for the service.

    Returns:
        A dictionary of dependency providers for the service.
    """
    svc = create_service_provider(service_class, statement, config, error_messages, load, execution_options)
    deps = {key: Provide(svc)}
    if filters:
        deps.update(create_filter_dependencies(filters))
    return deps


def create_filter_dependencies(config: FilterConfig) -> dict[str, Provide]:
    """Create a dependency provider for the combined filter function.

    Args:
        config: FilterConfig instance with desired settings.

    Returns:
        A dependency provider function for the combined filter function.
    """
    cache_key = sum(map(hash, config.items()))
    deps = dep_cache.get_dependencies(cache_key)
    if deps is not None:
        return deps
    deps = _create_statement_filters(config)
    dep_cache.add_dependencies(cache_key, deps)
    return deps


def _create_statement_filters(config: FilterConfig) -> dict[str, Provide]:  # noqa: C901
    """Create filter dependencies based on configuration.

    Args:
        config (FilterConfig): Configuration dictionary specifying which filters to enable

    Returns:
        dict[str, Provide]: Dictionary of filter provider functions
    """
    filters: dict[str, Provide] = {}

    if config.get("id_filter", False):

        def provide_id_filter(
            ids: list[str] | None = Parameter(query="ids", default=None, required=False),
        ) -> CollectionFilter:
            return CollectionFilter(field_name=config.get("id_field", "id"), values=ids)

        filters[ID_FILTER_DEPENDENCY_KEY] = Provide(provide_id_filter, sync_to_thread=False)

    if config.get("created_at", False):

        def provide_created_filter(
            before: DTorNone = Parameter(query="createdBefore", default=None, required=False),
            after: DTorNone = Parameter(query="createdAfter", default=None, required=False),
        ) -> BeforeAfter:
            return BeforeAfter("created_at", before, after)

        filters[CREATED_FILTER_DEPENDENCY_KEY] = Provide(provide_created_filter, sync_to_thread=False)

    if config.get("updated_at", False):

        def provide_updated_filter(
            before: DTorNone = Parameter(query="updatedBefore", default=None, required=False),
            after: DTorNone = Parameter(query="updatedAfter", default=None, required=False),
        ) -> BeforeAfter:
            return BeforeAfter("updated_at", before, after)

        filters[UPDATED_FILTER_DEPENDENCY_KEY] = Provide(provide_updated_filter, sync_to_thread=False)

    if config.get("pagination_type") == "limit_offset":

        def provide_limit_offset_pagination(
            current_page: int = Parameter(ge=1, query="currentPage", default=1, required=False),
            page_size: int = Parameter(
                query="pageSize",
                ge=1,
                default=config.get("pagination_size", DEFAULT_PAGINATION_SIZE),
                required=False,
            ),
        ) -> LimitOffset:
            return LimitOffset(page_size, page_size * (current_page - 1))

        filters[LIMIT_OFFSET_DEPENDENCY_KEY] = Provide(provide_limit_offset_pagination, sync_to_thread=False)

    if config.get("search", False):

        def provide_search_filter(
            field: StringOrNone = Parameter(title="Field to search", query="searchField", default=None, required=False),
            search: StringOrNone = Parameter(
                title="Field to search",
                query="searchString",
                default=None,
                required=False,
            ),
            ignore_case: BooleanOrNone = Parameter(
                title="Search should be case sensitive",
                query="searchIgnoreCase",
                default=config.get("search_ignore_case", False),
                required=False,
            ),
        ) -> SearchFilter:
            return SearchFilter(field_name=field, value=search, ignore_case=ignore_case or False)  # type: ignore[arg-type]

        filters[SEARCH_FILTER_DEPENDENCY_KEY] = Provide(provide_search_filter, sync_to_thread=False)

    if sort_field := config.get("sort_field"):

        def provide_order_by(
            field_name: StringOrNone = Parameter(
                title="Order by field",
                query="orderBy",
                default=sort_field,
                required=False,
            ),
            sort_order: SortOrderOrNone = Parameter(
                title="Field to search",
                query="sortOrder",
                default=config.get("sort_order", "desc"),
                required=False,
            ),
        ) -> OrderBy:
            return OrderBy(field_name=field_name, sort_order=sort_order)  # type: ignore[arg-type]

        filters[ORDER_BY_DEPENDENCY_KEY] = Provide(provide_order_by, sync_to_thread=False)
    if filters:
        filters[FILTERS_DEPENDENCY_KEY] = Provide(_create_filter_aggregate_function(config), sync_to_thread=False)

    return filters


def _create_filter_aggregate_function(config: FilterConfig) -> Callable[..., list[FilterTypes]]:  # noqa: C901
    """Create a filter function based on the provided configuration.

    Args:
        config: The filter configuration.

    Returns:
        A function that returns a list of filters based on the configuration.
    """

    parameters: dict[str, inspect.Parameter] = {}
    annotations: dict[str, Any] = {}

    # Build parameters based on config
    if cls := config.get("id_filter"):
        parameters["id_filter"] = inspect.Parameter(
            name="id_filter",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Dependency(skip_validation=True),
            annotation=CollectionFilter[cls],  # type: ignore[valid-type]
        )
        annotations["id_filter"] = CollectionFilter[cls]  # type: ignore[valid-type]

    if config.get("created_at"):
        parameters["created_filter"] = inspect.Parameter(
            name="created_filter",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Dependency(skip_validation=True),
            annotation=BeforeAfter,
        )
        annotations["created_filter"] = BeforeAfter

    if config.get("updated_at"):
        parameters["updated_filter"] = inspect.Parameter(
            name="updated_filter",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Dependency(skip_validation=True),
            annotation=BeforeAfter,
        )
        annotations["updated_filter"] = BeforeAfter

    if config.get("search"):
        parameters["search_filter"] = inspect.Parameter(
            name="search_filter",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Dependency(skip_validation=True),
            annotation=SearchFilter,
        )
        annotations["search_filter"] = SearchFilter

    if config.get("pagination_type") == "limit_offset":
        parameters["limit_offset"] = inspect.Parameter(
            name="limit_offset",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Dependency(skip_validation=True),
            annotation=LimitOffset,
        )
        annotations["limit_offset"] = LimitOffset

    if config.get("sort_field"):
        parameters["order_by"] = inspect.Parameter(
            name="order_by",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Dependency(skip_validation=True),
            annotation=OrderBy,
        )
        annotations["order_by"] = OrderBy

    def provide_filters(**kwargs: FilterTypes) -> list[FilterTypes]:
        """Provide filter dependencies based on configuration.

        Args:
            **kwargs: Filter parameters dynamically provided based on configuration.

        Returns:
            list[FilterTypes]: List of configured filters.
        """
        filters: list[FilterTypes] = []
        if id_filter := kwargs.get("id_filter"):
            filters.append(id_filter)
        if created_filter := kwargs.get("created_filter"):
            filters.append(created_filter)
        if limit_offset := kwargs.get("limit_offset"):
            filters.append(limit_offset)
        if updated_filter := kwargs.get("updated_filter"):
            filters.append(updated_filter)
        if (
            (search_filter := cast("SearchFilter | None", kwargs.get("search_filter")))
            and search_filter.field_name is not None
            and search_filter.value is not None
        ):
            filters.append(search_filter)
        if (order_by := cast("OrderBy | None", kwargs.get("order_by"))) and order_by.field_name is not None:
            filters.append(order_by)
        return filters

    # Set both signature and annotations
    provide_filters.__signature__ = inspect.Signature(  # type: ignore
        parameters=list(parameters.values()),
        return_annotation=list[FilterTypes],
    )
    provide_filters.__annotations__ = annotations
    provide_filters.__annotations__["return"] = list[FilterTypes]

    return provide_filters
