"""Application dependency providers."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from starlite.contrib.repository.filters import (
    BeforeAfter,
    CollectionFilter,
    LimitOffset,
)
from starlite.di import Provide
from starlite.params import Dependency, Parameter

from app.lib import constants

DTorNone = datetime | None

FilterTypes = BeforeAfter | CollectionFilter[Any] | LimitOffset
"""Aggregate type alias of the types supported for collection filtering."""
CREATED_FILTER_DEPENDENCY_KEY = "created_filter"
FILTERS_DEPENDENCY_KEY = "filters"
ID_FILTER_DEPENDENCY_KEY = "id_filter"
LIMIT_OFFSET_DEPENDENCY_KEY = "limit_offset"
UPDATED_FILTER_DEPENDENCY_KEY = "updated_filter"


def provide_id_filter(
    ids: list[UUID] | None = Parameter(query="ids", default=None, required=False),
) -> CollectionFilter[UUID]:
    """Return type consumed by ``Repository.filter_in_collection()``.

    Parameters
    ----------
    ids : list[UUID] | None
        Parsed out of comma separated list of values in query params.

    Returns
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
    return BeforeAfter("created", before, after)


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
    return BeforeAfter("updated", before, after)


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

    Returns
    -------
    list[FilterTypes]
        List of filters parsed from connection.
    """
    return [
        created_filter,
        id_filter,
        limit_offset,
        updated_filter,
    ]


def create_collection_dependencies() -> dict[str, Provide]:
    """Create ORM dependencies.

    Creates a dictionary of provides for pagination endpoints.

    Returns
    -------
    dict[str, Provide]

    """
    return {
        LIMIT_OFFSET_DEPENDENCY_KEY: Provide(provide_limit_offset_pagination),
        UPDATED_FILTER_DEPENDENCY_KEY: Provide(provide_updated_filter),
        CREATED_FILTER_DEPENDENCY_KEY: Provide(provide_created_filter),
        ID_FILTER_DEPENDENCY_KEY: Provide(provide_id_filter),
        FILTERS_DEPENDENCY_KEY: Provide(provide_filter_dependencies),
    }
