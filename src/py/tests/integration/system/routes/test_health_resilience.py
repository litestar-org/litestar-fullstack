from unittest.mock import patch

import pytest
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from litestar.testing import AsyncTestClient
from sqlalchemy.exc import OperationalError

from app.server.asgi import create_app

pytestmark = pytest.mark.anyio


async def test_health_endpoint_db_offline() -> None:
    """Test health endpoint returns 500 and offline status when DB is unreachable.

    It should catch OperationalError and not crash.
    """
    app = create_app()

    # Patch AsyncSession.execute to raise an OperationalError (like connection failed)
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.execute",
        side_effect=OperationalError("connection failed", None, Exception("orig")),
    ):
        async with AsyncTestClient(app=app) as client:
            response = await client.get("/health")

            assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["databaseStatus"] == "offline"
            assert "app" in data
