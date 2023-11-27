import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 500

    expected = {
        "database_status": "online",
        "cache_status": "online",
        "worker_status": "offline",
        "app": "Starlite Application",
        "version": "",
    }

    assert response.json() == expected
