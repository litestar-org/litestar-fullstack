from typing import TYPE_CHECKING

import pytest
from litestar import get
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

if TYPE_CHECKING:
    from httpx import AsyncClient
    from litestar import Litestar

pytestmark = pytest.mark.anyio


async def test_health(client: "AsyncClient") -> None:
    """Test health endpoint returns database status and app info.

    Note: Health endpoint is at /health, not /api/health - it's not behind the API prefix.
    """
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    # Check required fields are present
    assert data["databaseStatus"] == "online"  # Note: CamelizedBaseStruct converts to camelCase
    assert "app" in data and len(data["app"]) > 0  # App name should be present


async def test_db_session_dependency(app: "Litestar", engine: AsyncEngine, _patch_db: None) -> None:
    """Test that handlers receive session attached to patched engine.

    Note: _patch_db fixture ensures the app uses the test database engine.
    """

    @get("/db-session-test", opt={"exclude_from_auth": True})
    async def db_session_dependency_patched(db_session: AsyncSession) -> dict[str, str]:
        return {"result": f"{db_session.bind is engine = }"}

    app.register(db_session_dependency_patched)
    async with AsyncTestClient(app) as client:
        response = await client.get("/db-session-test")
        assert response.json()["result"] == "db_session.bind is engine = True"
