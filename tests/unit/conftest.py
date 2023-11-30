from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar import Litestar, get
from litestar.datastructures import State
from litestar.enums import ScopeType
from litestar.testing import AsyncTestClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from litestar.types import HTTPResponseBodyEvent, HTTPResponseStartEvent, HTTPScope

pytestmark = pytest.mark.anyio


@pytest.fixture(name="client")
async def fx_client(app: Litestar) -> AsyncGenerator[AsyncTestClient, None]:
    """Test client fixture for making calls on the global app instance."""
    try:
        async with AsyncTestClient(app=app) as client:
            yield client
    except Exception:  # noqa: BLE001
        ...


@pytest.fixture()
def http_response_start() -> HTTPResponseStartEvent:
    """ASGI message for start of response."""
    return {"type": "http.response.start", "status": 200, "headers": []}


@pytest.fixture()
def http_response_body() -> HTTPResponseBodyEvent:
    """ASGI message for interim, and final response body messages.

    Note:
        `more_body` is `True` for interim body messages.
    """
    return {"type": "http.response.body", "body": b"body", "more_body": False}


@pytest.fixture()
def state() -> State:
    """Litestar application state data structure."""
    return State()


@pytest.fixture()
def http_scope(app: Litestar) -> HTTPScope:
    """Minimal ASGI HTTP connection scope."""

    @get()
    async def handler() -> None:
        ...

    return {
        "headers": [],
        "app": app,
        "asgi": {"spec_version": "whatever", "version": "3.0"},
        "auth": None,
        "client": None,
        "extensions": None,
        "http_version": "3",
        "path": "/wherever",
        "path_params": {},
        "query_string": b"",
        "raw_path": b"/wherever",
        "root_path": "/",
        "route_handler": handler,
        "scheme": "http",
        "server": None,
        "session": {},
        "state": {},
        "user": None,
        "method": "GET",
        "type": ScopeType.HTTP,
    }
