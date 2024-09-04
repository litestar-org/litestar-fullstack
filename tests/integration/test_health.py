import pytest
from httpx import AsyncClient

from app.__about__ import __version__

pytestmark = pytest.mark.anyio


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200

    expected = {
        "database_status": "online",
        "cache_status": "online",
        "app": "app",
        "version": __version__,
    }

    assert response.json() == expected
