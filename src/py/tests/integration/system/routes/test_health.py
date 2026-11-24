"""Integration tests for system health and public auth configuration endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar import get
from litestar.testing import AsyncTestClient
from litestar_security import public

if TYPE_CHECKING:
    from httpx import AsyncClient
    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_health(client: AsyncClient) -> None:
    """Health endpoint returns online database and queue status with app metadata."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["databaseStatus"] == "online"
    assert data["queueStatus"] == "online"
    assert data["app"]


async def test_public_auth_config(client: AsyncClient) -> None:
    """Public auth configuration exposes boolean feature flags without authentication."""
    response = await client.get("/api/config/auth")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) >= {"googleEnabled", "githubEnabled", "passkeysEnabled", "mfaEnabled"}


async def test_db_session_dependency(app: Litestar, engine: AsyncEngine) -> None:
    """Handlers receive a database session bound to the worker PostgreSQL engine."""

    @get("/db-session-test", opt={"auth": public()})
    async def db_session_dependency_patched(db_session: AsyncSession) -> dict[str, bool]:
        return {"matched": db_session.bind is engine}

    app.register(db_session_dependency_patched)
    async with AsyncTestClient(app=app) as client:
        response = await client.get("/db-session-test")
        assert response.status_code == 200
        assert response.json() == {"matched": True}
