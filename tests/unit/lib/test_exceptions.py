from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import pytest
from litestar import Litestar, get
from litestar.repository.exceptions import ConflictError, NotFoundError
from litestar.status_codes import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from litestar.testing import RequestFactory, create_test_client

from app.lib import exceptions
from app.lib.exceptions import ApplicationError

if TYPE_CHECKING:
    from collections import abc


def test_after_exception_hook_handler_called(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests that the handler gets added to the app and called."""
    logger_mock = MagicMock()
    monkeypatch.setattr(exceptions, "bind_contextvars", logger_mock)
    exc = RuntimeError()

    @get("/error")
    async def raises() -> None:
        raise exc

    with create_test_client(
        route_handlers=[raises],
        after_exception=[exceptions.after_exception_hook_handler],
    ) as client:
        resp = client.get("/error")
        assert resp.status_code == HTTP_500_INTERNAL_SERVER_ERROR

    logger_mock.assert_called_once_with(exc_info=(RuntimeError, exc, ANY))


@pytest.mark.parametrize(
    ("exc", "status"),
    [
        (ConflictError, HTTP_409_CONFLICT),
        (NotFoundError, HTTP_404_NOT_FOUND),
        (ApplicationError, HTTP_500_INTERNAL_SERVER_ERROR),
    ],
)
def test_repository_exception_to_http_response(exc: type[ApplicationError], status: int) -> None:
    app = Litestar(route_handlers=[])
    request = RequestFactory(app=app, server="testserver").get("/wherever")
    response = exceptions.exception_to_http_response(request, exc())
    assert response.status_code == status


@pytest.mark.parametrize(
    ("exc", "status"),
    [
        (exceptions.AuthorizationError, HTTP_403_FORBIDDEN),
        (exceptions.ApplicationError, HTTP_500_INTERNAL_SERVER_ERROR),
    ],
)
def test_exception_to_http_response(exc: type[exceptions.ApplicationError], status: int) -> None:
    app = Litestar(route_handlers=[])
    request = RequestFactory(app=app, server="testserver").get("/wherever")
    response = exceptions.exception_to_http_response(request, exc())
    assert response.status_code == status


@pytest.mark.parametrize(
    ("exc", "fn", "expected_message"),
    [
        (
            exceptions.ApplicationError("message"),
            exceptions.exception_to_http_response,
            b"app.lib.exceptions.ApplicationError: message\n",
        ),
    ],
)
def test_exception_serves_debug_middleware_response(
    exc: Exception,
    fn: "abc.Callable",
    expected_message: bytes,
) -> None:
    app = Litestar(route_handlers=[], debug=True)
    request = RequestFactory(app=app, server="testserver").get("/wherever")
    response = fn(request, exc)
    assert response.content == expected_message.decode()
