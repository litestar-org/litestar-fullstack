"""Application dependency providers."""

from __future__ import annotations

import datetime
import hashlib
import inspect
import json
from collections.abc import Callable, Coroutine
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NotRequired,
    TypedDict,
    TypeVar,
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
from advanced_alchemy.service import (
    Empty,
    EmptyType,
    ErrorMessages,
    LoadSpec,
    ModelT,
    SQLAlchemyAsyncRepositoryService,
)
from litestar.di import Provide
from litestar.params import Parameter

from app.config import app as c

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from advanced_alchemy.config.asyncio import SQLAlchemyAsyncConfig
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession


DTorNone = datetime.datetime | None
StringOrNone = str | None
UuidOrNone = UUID | None
BooleanOrNone = bool | None
SortOrder = Literal["asc", "desc"]
SortOrderOrNone = SortOrder | None
PaginationTypes = Literal["limit_offset"]
IdentityT = TypeVar("IdentityT", bound=UUID | int)
ServiceT_co = TypeVar("ServiceT_co", bound=SQLAlchemyAsyncRepositoryService[Any], covariant=True)

DEFAULT_IDENTITY_FIELD: str = "id"
DEFAULT_PAGINATION_SIZE: int = 20

# Type alias for the filter function
FilterFunction = Callable[..., Coroutine[Any, Any, list[FilterTypes]]]

# Cache for generated filter functions
_FILTER_FUNCTION_CACHE: dict[str, FilterFunction] = {}


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


def _get_cache_key(config: FilterConfig) -> str:
    """Generate a unique cache key for a filter configuration.

    Args:
        config: The filter configuration to generate a key for.

    Returns:
        A unique string key for the configuration.
    """
    # Sort the config items to ensure consistent ordering
    sorted_items = sorted((k, str(v) if isinstance(v, type) else v) for k, v in config.items() if v is not None)
    # Convert to JSON string for hashing
    config_str = json.dumps(sorted_items, sort_keys=True)
    # Generate SHA256 hash
    return hashlib.sha256(config_str.encode()).hexdigest()


def _create_filter_function(config: FilterConfig) -> FilterFunction:
    """Create a filter function based on the provided configuration.

    Args:
        config: The filter configuration.

    Returns:
        A function that returns a list of filters based on the configuration.
    """
    id_field = config.get("id_field", DEFAULT_IDENTITY_FIELD)
    pagination_size = config.get("pagination_size", DEFAULT_PAGINATION_SIZE)
    search_fields = config.get("search_fields")
    case_sensitive = config.get("search_is_case_sensitive", False)
    sort_field = config.get("sort_field", "id")
    sort_order = config.get("sort_order", "desc")

    # Convert search_fields to set if it's a list
    search_fields_set: str | set[str] = set(search_fields) if isinstance(search_fields, list) else (search_fields or "")

    # Define parameters based on config
    parameters = {}

    if config.get("id_filter"):
        parameters["ids"] = Parameter(
            query="ids",
            required=False,
            default=None,
            annotation=list[config["id_filter"]],  # type: ignore # noqa: F821
        )

    if config.get("pagination_type"):
        parameters["current_page"] = Parameter(
            query="currentPage",
            required=False,
            default=1,
            ge=1,
            annotation=int,
        )

    if search_fields:
        parameters["search_value"] = Parameter(
            query="searchString",
            required=False,
            default=None,
            annotation=str,
        )

    if config.get("created_at"):
        parameters["created_before"] = Parameter(
            query="createdBefore",
            required=False,
            default=None,
            annotation=DTorNone,
        )
        parameters["created_after"] = Parameter(
            query="createdAfter",
            required=False,
            default=None,
            annotation=DTorNone,
        )

    if config.get("updated_at"):
        parameters["updated_before"] = Parameter(
            query="updatedBefore",
            required=False,
            default=None,
            annotation=DTorNone,
        )
        parameters["updated_after"] = Parameter(
            query="updatedAfter",
            required=False,
            default=None,
            annotation=DTorNone,
        )

    async def provide_filters(**kwargs: Any) -> list[FilterTypes]:
        """Provide filter dependencies based on configuration.

        Returns:
            list[FilterTypes]: List of configured filters.
        """
        filters: list[FilterTypes] = []

        # ID filter
        if kwargs.get("ids"):
            filters.append(
                CollectionFilter[config.get("id_filter", type[UUID | int])](field_name=id_field, values=kwargs["ids"]),
            )

        # Pagination
        filters.append(
            LimitOffset(
                limit=pagination_size,
                offset=pagination_size * (kwargs.get("current_page", 1) - 1),
            ),
        )

        # Search filter
        if kwargs.get("search_value") and search_fields_set:
            filters.append(
                SearchFilter(
                    field_name=search_fields_set,
                    value=kwargs["search_value"],
                    ignore_case=not case_sensitive,
                ),
            )

        # Created/Updated datetime filters
        if kwargs.get("created_before") or kwargs.get("created_after"):
            filters.append(
                BeforeAfter(
                    field_name="created_at",
                    operator="le" if kwargs.get("created_before") else "ge",
                    value=kwargs.get("created_before") or kwargs.get("created_after"),
                ),
            )

        if kwargs.get("updated_before") or kwargs.get("updated_after"):
            filters.append(
                BeforeAfter(
                    field_name="updated_at",
                    operator="le" if kwargs.get("updated_before") else "ge",
                    value=kwargs.get("updated_before") or kwargs.get("updated_after"),
                ),
            )

        # Sort order
        if sort_field:
            filters.append(OrderBy(field_name=sort_field, sort_order=sort_order))

        return filters

    # Create signature from parameters
    sig = inspect.Signature(
        parameters=[
            inspect.Parameter(
                name=name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=param,
                annotation=param.annotation,
            )
            for name, param in parameters.items()
        ],
        return_annotation=list[FilterTypes],
    )
    provide_filters.__signature__ = sig  # type: ignore
    return provide_filters


def create_filter_dependencies(config: FilterConfig) -> Provide:
    """Create a dependency provider that injects configured filters into a handler.

    This function is cached using LRU caching to avoid regenerating the same filter
    functions repeatedly. The cache key is based on the FilterConfig contents.

    Args:
        config: FilterConfig instance with desired settings.

    Returns:
        A dependency provider function that returns a list of filter instances.
    """
    cache_key = _get_cache_key(config)

    # if cache_key not in _FILTER_FUNCTION_CACHE:
    filter_func = _create_filter_function(config)
    _FILTER_FUNCTION_CACHE[cache_key] = filter_func

    return Provide(_FILTER_FUNCTION_CACHE[cache_key])


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
