"""Offline unit test ASGI fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar import Litestar, get
from litestar.datastructures import State
from litestar.enums import ScopeType

if TYPE_CHECKING:
    from litestar.types import HTTPResponseBodyEvent, HTTPResponseStartEvent, HTTPScope

pytestmark = pytest.mark.anyio


@pytest.fixture
def http_response_start() -> HTTPResponseStartEvent:
    """ASGI message for start of response."""
    return {"type": "http.response.start", "status": 200, "headers": []}


@pytest.fixture
def http_response_body() -> HTTPResponseBodyEvent:
    """ASGI message for interim and final response body messages."""
    return {"type": "http.response.body", "body": b"body", "more_body": False}


@pytest.fixture
def state() -> State:
    """Litestar application state data structure."""
    return State()


@pytest.fixture
def http_scope() -> HTTPScope:
    """Minimal ASGI HTTP connection scope for offline unit tests."""

    @get()
    async def handler() -> None:
        return None

    minimal_app = Litestar(route_handlers=[handler])
    return {
        "headers": [],
        "app": minimal_app,
        "litestar_app": minimal_app,
        "asgi": {"spec_version": "whatever", "version": "3.0"},
        "auth": None,
        "client": None,
        "extensions": None,
        "http_version": "3",
        "path": "/wherever",
        "path_params": {},
        "query_string": b"",
        "raw_path": b"/wherever",
        "path_template": "template.j2",
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
