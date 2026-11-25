from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError
from litestar import Litestar, get
from litestar.exceptions import HTTPException, PermissionDeniedException
from litestar.stores.memory import MemoryStore
from litestar.testing import AsyncTestClient
from litestar_autowire import AutowireConfig
from litestar_queues import QueueConfig, WorkerConfig

from app.lib.exceptions import (
    ApplicationError,
    AuthorizationError,
    exception_to_http_response,
)
from app.lib.validation import ValidationError
from app.server.core import ApplicationCore

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = pytest.mark.anyio

PROBLEM_JSON = "application/problem+json"


def test_application_error_init() -> None:
    exc = ApplicationError("msg", detail="detailed info")
    assert exc.detail == "detailed info"
    assert "msg" in str(exc)
    assert "detailed info" in str(exc)

    exc2 = ApplicationError("msg")
    assert exc2.detail == "msg"

    assert "ApplicationError" in repr(exc)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (NotFoundError("No tag found"), {"status": 404, "title": "Not Found", "detail": "No tag found"}),
        (AuthorizationError("Not your team"), {"status": 403, "title": "Forbidden", "detail": "Not your team"}),
        (DuplicateKeyError("Tag exists"), {"status": 409, "title": "Conflict", "detail": "Tag exists"}),
        (
            ValidationError("Name cannot be empty"),
            {"status": 400, "title": "Bad Request", "detail": "Name cannot be empty"},
        ),
        (
            ApplicationError("database password rejected"),
            {"status": 500, "title": "Internal Server Error", "detail": "Internal Server Error"},
        ),
    ],
)
def test_exception_to_http_response_describes_the_error_as_a_problem(exc: Exception, expected: dict[str, Any]) -> None:
    request = MagicMock()
    request.app.debug = False

    response = exception_to_http_response(request, exc)

    assert response.status_code == expected["status"]
    assert response.media_type == PROBLEM_JSON
    assert response.content == expected


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (NotFoundError("No tag found"), {"status": 404, "title": "Not Found", "detail": "No tag found"}),
        (AuthorizationError("Not your team"), {"status": 403, "title": "Forbidden", "detail": "Not your team"}),
    ],
)
def test_exception_to_http_response_keeps_not_found_and_authorization_problems_in_debug_mode(
    exc: Exception,
    expected: dict[str, Any],
) -> None:
    request = MagicMock()
    request.app.debug = True

    response = exception_to_http_response(request, exc)

    assert response.media_type == PROBLEM_JSON
    assert response.content == expected


def test_exception_to_http_response_renders_the_debug_page_in_debug_mode() -> None:
    request = MagicMock()
    request.app.debug = True

    with patch("app.lib.exceptions.create_debug_response") as mock_debug:
        exception_to_http_response(request, ValueError("internal error"))

    mock_debug.assert_called_once()


@get("/api/errors/plain", opt={"exclude_from_auth": True}, sync_to_thread=False)
def raise_plain_http_exception() -> None:
    raise HTTPException(detail="Slow down", status_code=429)


@get("/api/errors/coded", opt={"exclude_from_auth": True}, sync_to_thread=False)
def raise_coded_http_exception() -> None:
    raise PermissionDeniedException(detail="No access to this application", extra={"code": "access_required"})


@get("/api/errors/conflict", opt={"exclude_from_auth": True}, sync_to_thread=False)
def raise_repository_conflict() -> None:
    raise DuplicateKeyError(detail="A tag with this name already exists")


@get("/api/errors/invalid", opt={"exclude_from_auth": True}, sync_to_thread=False)
def raise_validation_error() -> None:
    msg = "Name cannot be empty"
    raise ValidationError(msg)


@pytest.fixture
async def client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    app = Litestar(
        route_handlers=[
            raise_plain_http_exception,
            raise_coded_http_exception,
            raise_repository_conflict,
            raise_validation_error,
        ],
        plugins=[
            ApplicationCore(
                autowire_config=AutowireConfig(domain_packages=[], integrations=[]),
                queue_config=QueueConfig(queue_backend="memory", worker=WorkerConfig(placement="external")),
            )
        ],
        stores={"sessions": MemoryStore()},
    )
    async with AsyncTestClient(app=app) as test_client:
        yield test_client


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/api/errors/plain", {"status": 429, "title": "Too Many Requests", "detail": "Slow down"}),
        (
            "/api/errors/coded",
            {"status": 403, "title": "Forbidden", "detail": "No access to this application", "code": "access_required"},
        ),
        ("/api/errors/conflict", {"status": 409, "title": "Conflict", "detail": "A tag with this name already exists"}),
        ("/api/errors/invalid", {"status": 400, "title": "Bad Request", "detail": "Name cannot be empty"}),
        ("/api/no-such-route", {"status": 404, "title": "Not Found", "detail": "Not Found"}),
    ],
)
async def test_every_error_response_uses_the_problem_details_envelope(
    client: AsyncTestClient[Litestar],
    path: str,
    expected: dict[str, Any],
) -> None:
    response = await client.get(path)

    assert response.status_code == expected["status"]
    assert response.headers["content-type"].startswith(PROBLEM_JSON)
    assert response.json() == expected
