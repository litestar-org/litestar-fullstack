"""Integration tests for degraded health reporting on database and queue outages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from litestar.status_codes import HTTP_503_SERVICE_UNAVAILABLE
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_health_endpoint_returns_503_when_db_offline(client: AsyncClient) -> None:
    """Health endpoint returns HTTP 503 with offline databaseStatus when PostgreSQL check fails."""
    original_execute = AsyncSession.execute

    async def _fail_health_probe(self: AsyncSession, statement: Any, *args: Any, **kwargs: Any) -> Any:
        if str(statement).strip().lower() == "select 1":
            msg = "db_offline"
            raise OperationalError(msg, None, Exception(msg))
        return await original_execute(self, statement, *args, **kwargs)

    with patch.object(AsyncSession, "execute", _fail_health_probe):
        response = await client.get("/health")

    assert response.status_code == HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["databaseStatus"] == "offline"
    assert data["queueStatus"] == "online"
    assert data["app"]


async def test_health_endpoint_returns_503_when_queue_offline(client: AsyncClient) -> None:
    """Health endpoint returns HTTP 503 with offline queueStatus when queue probe fails."""
    with patch("litestar_queues.QueueService.list_tasks", side_effect=RuntimeError("queue unavailable")):
        response = await client.get("/health")

    assert response.status_code == HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["databaseStatus"] == "online"
    assert data["queueStatus"] == "offline"
    assert data["app"]
