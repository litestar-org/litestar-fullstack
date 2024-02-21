from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Literal

import pytest
from advanced_alchemy.filters import (
    BeforeAfter,
    CollectionFilter,
    FilterTypes,
    LimitOffset,
    OrderBy,
    SearchFilter,
)
from litestar import Litestar, get
from litestar.params import Dependency
from litestar.testing import AsyncTestClient, RequestFactory
from uuid_utils import uuid4

from app.db.models import User
from app.domain import security
from app.lib import dependencies

if TYPE_CHECKING:
    from collections import abc

pytestmark = pytest.mark.anyio


@dataclass
class MessageTest:
    test_attr: str


async def test_provide_user_dependency() -> None:
    user = User()
    request = RequestFactory(app=Litestar(route_handlers=[])).get("/", user=user)
    assert await security.provide_user(request) is user


def test_id_filter() -> None:
    ids = [uuid4() for _ in range(3)]
    assert dependencies.provide_id_filter(ids) == CollectionFilter(field_name="id", values=ids)


@pytest.mark.parametrize(
    ("filter_", "field_name"),
    [(dependencies.provide_created_filter, "created_at"), (dependencies.provide_updated_filter, "updated_at")],
)
def test_before_after_filters(filter_: "abc.Callable[[datetime, datetime], BeforeAfter]", field_name: str) -> None:
    assert filter_(datetime.max, datetime.min) == BeforeAfter(
        field_name=field_name,
        before=datetime.max,
        after=datetime.min,
    )


@pytest.mark.parametrize(
    ("filter_", "field_name", "search_string", "ignore_case"),
    [
        (dependencies.provide_search_filter, "first_name", "co", True),
        (dependencies.provide_search_filter, "last_name", "Fin", False),
    ],
)
def test_search_filters(
    filter_: "abc.Callable[[str, str,bool], SearchFilter]",
    field_name: str,
    search_string: str,
    ignore_case: bool,
) -> None:
    assert filter_(field_name, search_string, ignore_case) == SearchFilter(
        field_name=field_name,
        value=search_string,
        ignore_case=ignore_case,
    )


@pytest.mark.parametrize(
    ("filter_", "field_name", "sort_order"),
    [
        (dependencies.provide_order_by, "first_name", "asc"),
        (dependencies.provide_order_by, "last_name", "desc"),
    ],
)
def test_order_by(
    filter_: "abc.Callable[[str, Literal['asc','desc']], OrderBy]",
    field_name: str,
    sort_order: Literal["asc", "desc"],
) -> None:
    assert filter_(field_name, sort_order) == OrderBy(field_name=field_name, sort_order=sort_order)


def test_limit_offset_pagination() -> None:
    assert dependencies.provide_limit_offset_pagination(10, 100) == LimitOffset(100, 900)


async def test_provided_filters(app: Litestar, client: AsyncTestClient) -> None:
    called = False
    path = f"/{uuid4()}"
    ids = [uuid4() for _ in range(2)]

    @get(
        path,
        opt={"exclude_from_auth": True},
    )
    async def filtered_collection_route(
        created_filter: BeforeAfter,
        updated_filter: BeforeAfter,
        limit_offset: LimitOffset,
        id_filter: CollectionFilter,
    ) -> MessageTest:
        nonlocal called
        assert created_filter == BeforeAfter("created_at", datetime.max, datetime.min)
        assert updated_filter == BeforeAfter("updated_at", datetime.max, datetime.min)
        assert limit_offset == LimitOffset(2, 18)
        assert id_filter == CollectionFilter("id", ids)
        called = True
        return MessageTest(test_attr="yay")

    app.register(filtered_collection_route)
    _response = await client.get(
        path,
        params={
            "createdBefore": datetime.max.isoformat(),
            "createdAfter": datetime.min.isoformat(),
            "updatedBefore": datetime.max.isoformat(),
            "updatedAfter": datetime.min.isoformat(),
            "currentPage": 10,
            "pageSize": 2,
            "ids": [str(id_) for id_ in ids],
        },
    )
    assert called


async def test_filters_dependency(app: "Litestar", client: "AsyncTestClient") -> None:
    called = False
    path = f"/{uuid4()}"
    ids = [uuid4() for _ in range(2)]

    @get(path=path, opt={"exclude_from_auth": True}, signature_namespace={"Dependency": Dependency})
    async def filtered_collection_route(
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> MessageTest:
        nonlocal called
        assert filters == [
            CollectionFilter(field_name="id", values=ids),
            BeforeAfter(field_name="created_at", before=datetime.max, after=datetime.min),
            LimitOffset(limit=2, offset=18),
            BeforeAfter(field_name="updated_at", before=datetime.max, after=datetime.min),
            SearchFilter(field_name="my_field", value="SearchString"),
            OrderBy(field_name="my_col", sort_order="desc"),
        ]
        called = True
        return MessageTest(test_attr="yay")

    app.debug = True
    app.register(filtered_collection_route)
    _response = await client.get(
        path,
        params={
            "createdBefore": datetime.max.isoformat(),
            "createdAfter": datetime.min.isoformat(),
            "updatedBefore": datetime.max.isoformat(),
            "updatedAfter": datetime.min.isoformat(),
            "currentPage": 10,
            "pageSize": 2,
            "ids": [str(id_) for id_ in ids],
            "orderBy": "my_col",
            "searchField": "my_field",
            "searchString": "SearchString",
        },
    )
    assert called


async def test_filters_dependency_no_ids(app: "Litestar", client: "AsyncTestClient") -> None:
    called = False
    path = f"/{uuid4()}"
    [uuid4() for _ in range(2)]

    @get(path=path, opt={"exclude_from_auth": True})
    async def filtered_collection_route(
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> MessageTest:
        nonlocal called
        assert filters == [
            BeforeAfter(field_name="created_at", before=datetime.max, after=datetime.min),
            LimitOffset(limit=2, offset=18),
            BeforeAfter(field_name="updated_at", before=datetime.max, after=datetime.min),
            SearchFilter(field_name="my_field", value="SearchString"),
            OrderBy(field_name="my_col", sort_order="desc"),
        ]
        called = True
        return MessageTest(test_attr="yay")

    app.debug = True
    app.register(filtered_collection_route)
    _response = await client.get(
        path,
        params={
            "createdBefore": datetime.max.isoformat(),
            "createdAfter": datetime.min.isoformat(),
            "updatedBefore": datetime.max.isoformat(),
            "updatedAfter": datetime.min.isoformat(),
            "currentPage": 10,
            "pageSize": 2,
            "orderBy": "my_col",
            "searchField": "my_field",
            "searchString": "SearchString",
        },
    )
    assert called
