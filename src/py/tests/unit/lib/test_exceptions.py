from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError
from litestar import Litestar, get, post
from litestar.exceptions import HTTPException, PermissionDeniedException
from litestar.stores.memory import MemoryStore
from litestar.testing import AsyncTestClient
from litestar_autowire import AutowireConfig
from litestar_queues import QueueConfig, WorkerConfig

from app.lib.exceptions import (
    ApplicationClientError,
    ApplicationError,
    AuthorizationError,
    exception_to_http_response,
)
from app.lib.schema import CamelizedBaseStruct, Username
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
            ApplicationClientError("Name cannot be empty"),
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
def raise_client_error() -> None:
    msg = "Name cannot be empty"
    raise ApplicationClientError(msg)


@get("/api/errors/crash", opt={"exclude_from_auth": True}, sync_to_thread=False)
def raise_unexpected_error() -> None:
    msg = "database password rejected"
    raise RuntimeError(msg)


class Signup(CamelizedBaseStruct):
    user_name: Username


@post("/api/errors/constrained", opt={"exclude_from_auth": True, "exclude_from_csrf": True}, sync_to_thread=False)
def accept_constrained_body(data: Signup) -> None:
    """Accept a body whose only field carries declarative constraints."""


@pytest.fixture
async def client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    app = Litestar(
        route_handlers=[
            raise_plain_http_exception,
            raise_coded_http_exception,
            raise_repository_conflict,
            raise_client_error,
            raise_unexpected_error,
            accept_constrained_body,
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


async def test_a_field_that_breaks_its_constraints_is_named_in_the_problem(client: AsyncTestClient[Litestar]) -> None:
    response = await client.post("/api/errors/constrained", json={"userName": "ab"})

    assert response.status_code == 400
    assert response.headers["content-type"].startswith(PROBLEM_JSON)
    assert response.json() == {
        "status": 400,
        "title": "Bad Request",
        "detail": "Validation failed for POST /api/errors/constrained",
        "extra": [{"message": "Expected `str` of length >= 3", "key": "userName", "source": "body"}],
    }


async def test_only_server_errors_log_a_stack_trace(
    client: AsyncTestClient[Litestar],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths_logged_with_a_stack_trace: list[str] = []

    class RecordingLogger:
        def error(self, event: str, *, path: str, exc_info: BaseException, **fields: Any) -> None:
            assert event == "Uncaught exception"
            assert isinstance(exc_info, RuntimeError)
            paths_logged_with_a_stack_trace.append(path)

    monkeypatch.setattr(client.app, "logger", RecordingLogger())

    statuses = [
        (await client.get(path)).status_code
        for path in (
            "/api/errors/invalid",
            "/api/errors/coded",
            "/api/no-such-route",
            "/api/errors/conflict",
            "/api/errors/plain",
            "/api/errors/crash",
        )
    ]
    statuses.append((await client.post("/api/errors/constrained", json={"userName": "ab"})).status_code)

    assert statuses == [400, 403, 404, 409, 429, 500, 400]
    assert paths_logged_with_a_stack_trace == ["/api/errors/crash"]
