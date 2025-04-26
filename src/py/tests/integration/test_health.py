import pytest
from httpx import AsyncClient

from app.__about__ import __version__

pytestmark = pytest.mark.anyio


@pytest.mark.xfail(reason="Flakey connection to service sometimes causes failures.")
async def test_health(client: AsyncClient, valkey_service: None) -> None:
    response = await client.get("/health")
    assert response.status_code == 200

    expected = {
        "database_status": "online",
        "cache_status": "online",
        "app": "app",
        "version": __version__,
    }

    assert response.json() == expected
