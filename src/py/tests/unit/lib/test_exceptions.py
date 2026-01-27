from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import pytest
from litestar.exceptions import (
    NotFoundException,
    PermissionDeniedException,
)
from litestar.repository.exceptions import NotFoundError

from app.lib.exceptions import (
    ApplicationError,
    AuthorizationError,
    after_exception_hook_handler,
    exception_to_http_response,
)

if TYPE_CHECKING:
    from litestar.types import Scope

pytestmark = pytest.mark.anyio


def test_application_error_init() -> None:
    exc = ApplicationError("msg", detail="detailed info")
    assert exc.detail == "detailed info"
    assert "msg" in str(exc)
    assert "detailed info" in str(exc)

    exc2 = ApplicationError("msg")
    assert exc2.detail == "msg"

    assert "ApplicationError" in repr(exc)


def test_after_exception_hook_handler_app_error() -> None:
    exc = ApplicationError("test")
    scope = cast("Scope", {})
    with patch("app.lib.exceptions.bind_contextvars") as mock_bind:
        after_exception_hook_handler(exc, scope)
        mock_bind.assert_not_called()


def test_after_exception_hook_handler_other_error() -> None:
    exc = ValueError("test")
    scope = cast("Scope", {})
    with patch("app.lib.exceptions.bind_contextvars") as mock_bind:
        after_exception_hook_handler(exc, scope)
        mock_bind.assert_called_once()


async def test_exception_to_http_response_not_found() -> None:
    request = MagicMock()
    request.app.debug = False
    exc = NotFoundError("not found")

    with patch("app.lib.exceptions.create_exception_response") as mock_create:
        exception_to_http_response(request, exc)
        args, _ = mock_create.call_args
        assert isinstance(args[1], NotFoundException)


async def test_exception_to_http_response_auth_error() -> None:
    request = MagicMock()
    request.app.debug = False
    exc = AuthorizationError("unauthorized")

    with patch("app.lib.exceptions.create_exception_response") as mock_create:
        exception_to_http_response(request, exc)
        args, _ = mock_create.call_args
        assert isinstance(args[1], PermissionDeniedException)


async def test_exception_to_http_response_debug() -> None:
    request = MagicMock()
    request.app.debug = True
    exc = ValueError("internal error")  # Will hit 'else' -> InternalServerException

    with patch("app.lib.exceptions.create_debug_response") as mock_debug:
        exception_to_http_response(request, exc)
        mock_debug.assert_called_once()
