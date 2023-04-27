# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar import Litestar, get
from litestar.datastructures import State
from litestar.enums import ScopeType

if TYPE_CHECKING:
    from litestar.types import HTTPResponseBodyEvent, HTTPResponseStartEvent, HTTPScope


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
    def handler() -> None:
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
