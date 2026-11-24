"""Integration tests for ``AsyncAPIPlugin`` schema exposure and secured ``/api/queues/events`` streams."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar.exceptions import WebSocketDisconnect

if TYPE_CHECKING:
    from httpx import AsyncClient
    from litestar import Litestar

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.endpoints]


async def test_asyncapi_schema_exposes_queue_events_channel(
    authenticated_client: AsyncClient,
) -> None:
    """Authenticated ``GET /asyncapi/asyncapi.json`` publishes the ``queue_events`` channel and payload schema."""
    response = await authenticated_client.get("/asyncapi/asyncapi.json")
    assert response.status_code == 200, response.text
    schema = response.json()

    channels = schema.get("channels", {})
    assert "queue_events" in channels
    assert channels["queue_events"]["address"] == "/api/queues/events"

    component_schemas = schema.get("components", {}).get("schemas", {})
    payload_schema = next(
        (definition for name, definition in component_schemas.items() if "QueueTaskEventPayload" in name),
        None,
    )
    assert payload_schema is not None
    properties = set(payload_schema.get("properties", {}).keys())
    assert {"taskId", "taskName", "queue", "status", "timestamp"}.issubset(properties)


async def test_queue_events_sse_rejects_unauthenticated_and_non_superuser_global(
    client: AsyncClient,
    test_user: object,
) -> None:
    """Unauthenticated callers get 401 on AsyncAPI/SSE streams and regular users get 403 on the global stream."""
    _ = test_user
    from tests.integration.conftest import login_session_client

    assert (await client.get("/asyncapi/asyncapi.json")).status_code == 401
    assert (await client.get("/api/queues/events/sse/global")).status_code == 401

    await login_session_client(client, "authuser@example.com", "TestPassword123!")
    assert (await client.get("/api/queues/events/sse/global")).status_code == 403


async def test_queue_events_websocket_rejects_unauthenticated(app: Litestar, db_cleanup: None) -> None:
    """Unauthenticated WebSocket upgrade attempts to ``/api/queues/events/global`` are rejected."""
    _ = db_cleanup
    from litestar.testing import TestClient

    with (
        TestClient(app=app) as sync_client,
        pytest.raises((WebSocketDisconnect, Exception)),
        sync_client.websocket_connect("/api/queues/events/global"),
    ):
        pass
