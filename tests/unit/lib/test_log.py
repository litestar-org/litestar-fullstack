from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog
from litestar import Request, get, post
from litestar.connection.base import empty_receive
from litestar.constants import SCOPE_STATE_RESPONSE_COMPRESSED
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from litestar.testing import RequestFactory
from litestar.utils.scope import set_litestar_scope_state
from structlog import DropEvent

from app.domain import urls
from app.lib import log, settings

try:
    import re2 as re  # pyright: ignore
except ImportError:
    import re

if TYPE_CHECKING:
    from typing import Any

    from litestar import Litestar
    from litestar.datastructures import State
    from litestar.testing import TestClient
    from litestar.types.asgi_types import (
        HTTPResponseBodyEvent,
        HTTPResponseStartEvent,
        HTTPScope,
    )
    from pytest import MonkeyPatch
    from structlog.testing import CapturingLogger


@pytest.fixture(name="before_send_handler")
def fx_before_send_handler() -> log.controller.BeforeSendHandler:
    """Callable that receives send messages on their way out to the client."""
    return log.controller.BeforeSendHandler()


def test_drop_health_logs_raises_structlog_drop_event() -> None:
    """Health check shouldn't be logged if successful."""
    with pytest.raises(DropEvent):
        log.controller.drop_health_logs(
            None,
            "abc",
            {
                "event": settings.log.HTTP_EVENT,
                "request": {"path": urls.SYSTEM_HEALTH},
                "response": {"status_code": HTTP_200_OK},
            },
        )


def test_drop_health_log_no_drop_event_if_not_success_status() -> None:
    """Healthcheck should be logged if it fails."""
    event_dict = {
        "event": settings.log.HTTP_EVENT,
        "request": {"path": urls.SYSTEM_HEALTH},
        "response": {"status_code": HTTP_500_INTERNAL_SERVER_ERROR},
    }
    assert event_dict == log.controller.drop_health_logs(None, "abc", event_dict)


def test_middleware_factory_added_to_app(app: Litestar) -> None:
    """Ensures the plugin adds the middleware to clear the context."""
    assert log.controller.middleware_factory in app.middleware


async def test_middleware_calls_structlog_contextvars_clear_contextvars(
    monkeypatch: MonkeyPatch,
) -> None:
    """Ensure that we clear the structlog context in the middleware."""
    clear_ctx_vars_mock = MagicMock()
    monkeypatch.setattr(structlog.contextvars, "clear_contextvars", clear_ctx_vars_mock)
    app_mock = AsyncMock()
    middleware = log.controller.middleware_factory(app_mock)
    await middleware(1, 2, 3)  # type:ignore[arg-type]
    clear_ctx_vars_mock.assert_called_once()
    app_mock.assert_called_once_with(1, 2, 3)


@pytest.mark.parametrize(
    ("pattern", "excluded", "included"),
    [
        ("^/a", ["/a", "/abc", "/a/b/c"], ["/b", "/b/a"]),
        ("a$", ["/a", "/cba", "/c/b/gorilla"], ["/a/b/c", "/armadillo"]),
        ("/a|/b", ["/a", "/b", "/a/b", "/b/a", "/ab", "/ba"], ["/c", "/not-a", "/not-b"]),
    ],
)
async def test_before_send_handler_exclude_paths(
    pattern: str,
    excluded: list[str],
    included: list[str],
    before_send_handler: log.controller.BeforeSendHandler,
    http_response_start: HTTPResponseStartEvent,
    http_scope: HTTPScope,
    state: State,
) -> None:
    """Test that exclude paths regex is respected.

    For each pattern, we ensure that each path in `excluded` is
    excluded, and each path in `included` is not excluded.
    """
    before_send_handler.exclude_paths = re.compile(pattern)

    async def call_handler(path_: str) -> dict[str, Any]:
        http_scope["path"] = path_
        http_scope["state"] = {}
        await before_send_handler(http_response_start, state, http_scope)
        return http_scope["state"]

    for path in excluded:
        assert {} == await call_handler(path)

    for path in included:
        scope_state = await call_handler(path)
        # scope state will be modified if path not excluded
        assert "log_level" in scope_state
        assert "http.response.start" in scope_state


@pytest.mark.parametrize(
    ("status", "level"),
    [
        (HTTP_200_OK, logging.INFO),
        (HTTP_500_INTERNAL_SERVER_ERROR, logging.ERROR),
    ],
)
async def test_before_send_handler_http_response_start(
    status: int,
    level: int,
    http_response_start: HTTPResponseStartEvent,
    before_send_handler: log.controller.BeforeSendHandler,
    http_scope: HTTPScope,
    state: State,
) -> None:
    """Test before send handler.

    When handler receives a response start event, it should store the
    message in the connection state for later logging, and also use the status
    code to determine the severity of the eventual log.
    """
    http_response_start["status"] = status
    assert http_scope["state"] == {}
    await before_send_handler(http_response_start, state, http_scope)
    assert http_scope["state"]["log_level"] == level
    assert http_scope["state"]["http.response.start"] == http_response_start


async def test_before_send_handler_http_response_body_with_more_body(
    before_send_handler: log.controller.BeforeSendHandler,
    cap_logger: CapturingLogger,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
    state: State,
) -> None:
    """We ignore intermediate response body messages, so should be a noop."""
    http_response_body["more_body"] = True
    await before_send_handler(http_response_body, state, http_scope)
    assert [] == cap_logger.calls


async def test_before_send_handler_http_response_body_without_more_body(
    before_send_handler: log.controller.BeforeSendHandler,
    cap_logger: CapturingLogger,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
    state: State,
    monkeypatch: MonkeyPatch,
) -> None:
    """We ignore intermediate response body messages, so should be a noop."""
    log_request_mock = AsyncMock()
    log_response_mock = AsyncMock()
    monkeypatch.setattr(log.controller.BeforeSendHandler, "log_request", log_request_mock)
    monkeypatch.setattr(log.controller.BeforeSendHandler, "log_response", log_response_mock)
    # this would have been added by the response start event handling
    http_scope["state"]["log_level"] = logging.INFO

    assert http_response_body["more_body"] is False
    await before_send_handler(http_response_body, state, http_scope)

    log_request_mock.assert_called_once_with(http_scope)
    log_response_mock.assert_called_once_with(http_scope)
    assert cap_logger.calls


async def test_before_send_handler_http_response_body_without_more_body_do_log_request_false(
    before_send_handler: log.controller.BeforeSendHandler,
    cap_logger: CapturingLogger,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
    state: State,
    monkeypatch: MonkeyPatch,
) -> None:
    """We ignore intermediate response body messages, so should be a noop."""
    log_request_mock = AsyncMock()
    log_response_mock = AsyncMock()
    monkeypatch.setattr(log.controller.BeforeSendHandler, "log_request", log_request_mock)
    monkeypatch.setattr(log.controller.BeforeSendHandler, "log_response", log_response_mock)
    # this would have been added by the response start event handling
    http_scope["state"]["log_level"] = logging.INFO

    assert http_response_body["more_body"] is False
    before_send_handler.do_log_request = False
    before_send_handler.do_log_response = False
    await before_send_handler(http_response_body, state, http_scope)

    log_request_mock.assert_not_called()
    log_response_mock.assert_not_called()
    assert cap_logger.calls


async def test_before_send_handler_does_nothing_with_other_message_types(
    before_send_handler: log.controller.BeforeSendHandler,
    cap_logger: CapturingLogger,
    http_scope: HTTPScope,
    state: State,
) -> None:
    """We are only interested in the `http.response.{start,body}` messages."""
    message = {"type": "cats.and.dogs"}
    await before_send_handler(message, state, http_scope)  # type:ignore[arg-type]
    assert [] == cap_logger.calls


async def test_before_send_handler_log_request(
    before_send_handler: log.controller.BeforeSendHandler,
    http_scope: HTTPScope,
    monkeypatch: MonkeyPatch,
) -> None:
    """Checks that the `log_request()` method does what it should."""
    ret_val = {"a": "b"}
    extractor_mock = AsyncMock(return_value=ret_val)
    bind_mock = MagicMock()
    monkeypatch.setattr(log.controller.BeforeSendHandler, "extract_request_data", extractor_mock)
    monkeypatch.setattr(structlog.contextvars, "bind_contextvars", bind_mock)
    await before_send_handler.log_request(http_scope)
    extractor_mock.assert_called_once()
    bind_mock.assert_called_once_with(request=ret_val)


async def test_before_send_handler_log_response(
    before_send_handler: log.controller.BeforeSendHandler,
    http_scope: HTTPScope,
    monkeypatch: MonkeyPatch,
) -> None:
    """Checks that the `log_response()` method does what it should."""
    ret_val = {"a": "b"}
    extractor_mock = MagicMock(return_value=ret_val)
    bind_mock = MagicMock()
    monkeypatch.setattr(log.controller.BeforeSendHandler, "extract_response_data", extractor_mock)
    monkeypatch.setattr(structlog.contextvars, "bind_contextvars", bind_mock)
    await before_send_handler.log_response(http_scope)
    extractor_mock.assert_called_once_with(scope=http_scope)
    bind_mock.assert_called_once_with(response=ret_val)


@pytest.mark.parametrize("include", [True, False])
async def test_before_send_handler_exclude_body_from_log(
    include: bool,
    before_send_handler: log.controller.BeforeSendHandler,
    http_response_start: HTTPResponseStartEvent,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
    monkeypatch: MonkeyPatch,
) -> None:
    """Check inclusion/exclusion of 'body' key in `log_response()."""
    if "body" not in settings.log.RESPONSE_FIELDS:
        settings.log.RESPONSE_FIELDS.append("body")
    set_litestar_scope_state(http_scope, SCOPE_STATE_RESPONSE_COMPRESSED, True)
    ret_val = {"body": "something random here."}
    extractor_mock = MagicMock(return_value=ret_val)
    monkeypatch.setattr(log.controller.BeforeSendHandler, "response_extractor", extractor_mock)
    monkeypatch.setattr(log.controller.BeforeSendHandler, "include_compressed_body", include)
    http_scope["state"]["http.response.start"] = http_response_start
    http_scope["state"]["http.response.body"] = http_response_body
    data = before_send_handler.extract_response_data(http_scope)
    extractor_mock.assert_called_once_with(messages=(http_response_start, http_response_body))
    if include:
        assert "body" in data
    else:
        assert "body" not in data


async def test_before_send_handler_extract_request_data(
    before_send_handler: log.controller.BeforeSendHandler,
) -> None:
    """I/O test for extract_request_data() method."""
    if "body" not in settings.log.RESPONSE_FIELDS:
        settings.log.RESPONSE_FIELDS.append("body")
    request = RequestFactory().post("/", data={"a": "b"})
    data = await before_send_handler.extract_request_data(request)
    assert data == {
        "body": b'{"a": "b"}',
        "path": "/",
        "method": "POST",
        "headers": {
            "content-length": "10",
            "content-type": "application/json",
        },
        "cookies": {},
        "query": b"",
        "path_params": {},
    }


def test_before_send_handler_extract_response_data(
    before_send_handler: log.controller.BeforeSendHandler,
    http_response_start: HTTPResponseStartEvent,
    http_response_body: HTTPResponseBodyEvent,
    http_scope: HTTPScope,
) -> None:
    """I/O test for extract_response_data() method."""
    http_scope["state"]["http.response.start"] = http_response_start
    http_scope["state"]["http.response.body"] = http_response_body
    data = before_send_handler.extract_response_data(http_scope)
    assert data == {"status_code": 200, "cookies": {}, "headers": {}, "body": b"body"}


async def test_exception_in_before_send_handler(
    client: TestClient[Litestar],
    cap_logger: CapturingLogger,
    monkeypatch: MonkeyPatch,
) -> None:
    """Test before send handler.

    Test we handle errors originating from trying to log a request in the
    before-send handler.
    """

    @get(path="/a/b/a/d", media_type="text/plain", opt={"exclude_from_auth": True})
    async def test_handler() -> str:
        return "Hello"

    monkeypatch.setattr(
        log.controller.BeforeSendHandler,
        "log_response",
        AsyncMock(side_effect=RuntimeError),
    )
    client.app.register(test_handler)
    resp = client.get("/a/b/a/d")
    assert resp.text == "Hello"
    assert len(cap_logger.calls) == 1
    call = cap_logger.calls[0]
    assert call.method_name == "error"
    assert call.kwargs["event"] == "Error in logging before-send handler!"
    assert call.kwargs["level"] == "error"


async def test_exception_in_before_send_handler_read_empty_body(
    client: TestClient[Litestar],
    cap_logger: CapturingLogger,
    before_send_handler: log.controller.BeforeSendHandler,
    http_scope: HTTPScope,
) -> None:
    """Test before send empty body.

    Test we handle errors originating from trying to log a request in the
    before-send handler.
    """
    if "body" not in settings.log.RESPONSE_FIELDS:
        settings.log.RESPONSE_FIELDS.append("body")

    @post(path="/1/2/3/4", media_type="text/plain", opt={"exclude_from_auth": True})
    async def test_handler() -> str:
        return "Hello"

    request: Request = Request(http_scope, receive=empty_receive)
    await before_send_handler.extract_request_data(request)

    client.app.register(test_handler)
    resp = client.post("/1/2/3/4")
    assert resp.text == "Hello"
    assert len(cap_logger.calls) == 1
    call = cap_logger.calls[0]
    assert call.method_name == "info"
    assert call.kwargs["event"] == "HTTP"
    assert bool("body" not in call.kwargs["request"] or getattr(call.kwargs["request"], "body", None) is None)
    assert call.kwargs["level"] == "info"


async def test_log_request_with_invalid_json_payload(client: TestClient[Litestar]) -> None:
    """Test logs emitted with invalid client payload.

    The request will fail with a 400 due to the data not being
    parsable, so we need to make sure that the logging doesn't also
    fail due to attempting to parse the invalid payload.
    """
    if "body" not in settings.log.RESPONSE_FIELDS:
        settings.log.RESPONSE_FIELDS.append("body")

    @post(opt={"exclude_from_auth": True})
    async def test_handler(data: dict[str, Any]) -> dict[str, Any]:
        return data

    client.app.register(test_handler)
    resp = client.post("/", content=b'{"a": "b",}', headers={"content-type": "application/json"})
    assert resp.status_code == HTTP_400_BAD_REQUEST


def test_event_filter() -> None:
    """Functionality test for the event filter processor."""
    event_filter = log.utils.EventFilter(["a_key"])
    log_event = {"a_key": "a_val", "b_key": "b_val"}
    log_event = event_filter(..., "", log_event)  # type:ignore[assignment]
    assert log_event == {"b_key": "b_val"}
