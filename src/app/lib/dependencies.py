"""Application dependency providers."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from advanced_alchemy.filters import (
    BeforeAfter,
    CollectionFilter,
    FilterTypes,
    LimitOffset,
    OrderBy,
    SearchFilter,
)
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app.lib import constants

__all__ = [
    "create_collection_dependencies",
    "provide_created_filter",
    "provide_filter_dependencies",
    "provide_id_filter",
    "provide_limit_offset_pagination",
    "provide_updated_filter",
    "provide_search_filter",
    "provide_order_by",
    "BeforeAfter",
    "CollectionFilter",
    "LimitOffset",
    "OrderBy",
    "SearchFilter",
    "FilterTypes",
]

DTorNone = datetime | None
StringOrNone = str | None
UuidOrNone = UUID | None
BooleanOrNone = bool | None
SortOrderOrNone = Literal["asc", "desc"] | None
"""Aggregate type alias of the types supported for collection filtering."""
FILTERS_DEPENDENCY_KEY = "filters"
CREATED_FILTER_DEPENDENCY_KEY = "created_filter"
ID_FILTER_DEPENDENCY_KEY = "id_filter"
LIMIT_OFFSET_DEPENDENCY_KEY = "limit_offset"
UPDATED_FILTER_DEPENDENCY_KEY = "updated_filter"
ORDER_BY_DEPENDENCY_KEY = "order_by"
SEARCH_FILTER_DEPENDENCY_KEY = "search_filter"


def provide_id_filter(
    ids: list[UUID] | None = Parameter(query="ids", default=None, required=False),
) -> CollectionFilter[UUID]:
    """Return type consumed by ``Repository.filter_in_collection()``.

    Parameters
    ----------
    ids : list[UUID] | None
        Parsed out of comma separated list of values in query params.

    Returns:
    -------
    CollectionFilter[UUID]
    """
    return CollectionFilter(field_name="id", values=ids or [])


def provide_created_filter(
    before: DTorNone = Parameter(query="createdBefore", default=None, required=False),
    after: DTorNone = Parameter(query="createdAfter", default=None, required=False),
) -> BeforeAfter:
    """Return type consumed by `Repository.filter_on_datetime_field()`.

    Parameters
    ----------
    before : datetime | None
        Filter for records updated before this date/time.
    after : datetime | None
        Filter for records updated after this date/time.
    """
    return BeforeAfter("created_at", before, after)


def provide_search_filter(
    field: StringOrNone = Parameter(title="Field to search", query="searchField", default=None, required=False),
    search: StringOrNone = Parameter(title="Field to search", query="searchString", default=None, required=False),
    ignore_case: BooleanOrNone = Parameter(
        title="Search should be case sensitive",
        query="searchIgnoreCase",
        default=None,
        required=False,
    ),
) -> SearchFilter:
    """Add offset/limit pagination.

    Return type consumed by `Repository.apply_search_filter()`.

    Parameters
    ----------
    field : int
        LIMIT to apply to select.
    page_size : int
        OFFSET to apply to select.
    """
    return SearchFilter(field_name=field, value=search, ignore_case=ignore_case or False)  # type: ignore[arg-type]


def provide_order_by(
    field_name: StringOrNone = Parameter(title="Order by field", query="orderBy", default=None, required=False),
    sort_order: SortOrderOrNone = Parameter(title="Field to search", query="sortOrder", default="desc", required=False),
) -> OrderBy:
    """Add offset/limit pagination.

    Return type consumed by `Repository.apply_order_by()`.

    Parameters
    ----------
    field_name : str
        Field name to order by.
    sort_order : str
        Order field ascending ('asc') or descending ('desc)
    """
    return OrderBy(field_name=field_name, sort_order=sort_order)  # type: ignore[arg-type]


def provide_updated_filter(
    before: DTorNone = Parameter(query="updatedBefore", default=None, required=False),
    after: DTorNone = Parameter(query="updatedAfter", default=None, required=False),
) -> BeforeAfter:
    """Add updated filter.

    Return type consumed by `Repository.filter_on_datetime_field()`.

    Parameters
    ----------
    before : datetime | None
        Filter for records updated before this date/time.
    after : datetime | None
        Filter for records updated after this date/time.
    """
    return BeforeAfter("updated_at", before, after)


def provide_limit_offset_pagination(
    current_page: int = Parameter(ge=1, query="currentPage", default=1, required=False),
    page_size: int = Parameter(
        query="pageSize",
        ge=1,
        default=constants.DEFAULT_PAGINATION_SIZE,
        required=False,
    ),
) -> LimitOffset:
    """Add offset/limit pagination.

    Return type consumed by `Repository.apply_limit_offset_pagination()`.

    Parameters
    ----------
    current_page : int
        LIMIT to apply to select.
    page_size : int
        OFFSET to apply to select.
    """
    return LimitOffset(page_size, page_size * (current_page - 1))


def provide_filter_dependencies(
    created_filter: BeforeAfter = Dependency(skip_validation=True),
    updated_filter: BeforeAfter = Dependency(skip_validation=True),
    id_filter: CollectionFilter = Dependency(skip_validation=True),
    limit_offset: LimitOffset = Dependency(skip_validation=True),
    search_filter: SearchFilter = Dependency(skip_validation=True),
    order_by: OrderBy = Dependency(skip_validation=True),
) -> list[FilterTypes]:
    """Provide common collection route filtering dependencies.

    Add all filters to any route by including this function as a dependency, e.g:

        @get
        def get_collection_handler(filters: Filters) -> ...:
            ...
    The dependency is provided at the application layer, so only need to inject the dependency where
    necessary.

    Parameters
    ----------
    id_filter : repository.CollectionFilter
        Filter for scoping query to limited set of identities.
    created_filter : repository.BeforeAfter
        Filter for scoping query to instance creation date/time.
    updated_filter : repository.BeforeAfter
        Filter for scoping query to instance update date/time.
    limit_offset : repository.LimitOffset
        Filter for query pagination.
    search_filter : repository.SearchFilter
        Filter for searching fields.
    order_by : repository.OrderBy
        Order by for query.


    Returns:
    -------
    list[FilterTypes]
        List of filters parsed from connection.
    """
    filters: list[FilterTypes] = []
    if id_filter.values:  # noqa: PD011
        filters.append(id_filter)
    filters.extend([created_filter, limit_offset, updated_filter])

    if search_filter.field_name is not None and search_filter.value is not None:
        filters.append(search_filter)
    if order_by.field_name is not None:
        filters.append(order_by)
    return filters


def create_collection_dependencies() -> dict[str, Provide]:
    """Create ORM dependencies.

    Creates a dictionary of provides for pagination endpoints.

    Returns:
    -------
    dict[str, Provide]
    """
    return {
        LIMIT_OFFSET_DEPENDENCY_KEY: Provide(provide_limit_offset_pagination, sync_to_thread=False),
        UPDATED_FILTER_DEPENDENCY_KEY: Provide(provide_updated_filter, sync_to_thread=False),
        CREATED_FILTER_DEPENDENCY_KEY: Provide(provide_created_filter, sync_to_thread=False),
        ID_FILTER_DEPENDENCY_KEY: Provide(provide_id_filter, sync_to_thread=False),
        SEARCH_FILTER_DEPENDENCY_KEY: Provide(provide_search_filter, sync_to_thread=False),
        ORDER_BY_DEPENDENCY_KEY: Provide(provide_order_by, sync_to_thread=False),
        FILTERS_DEPENDENCY_KEY: Provide(provide_filter_dependencies, sync_to_thread=False),
    }
