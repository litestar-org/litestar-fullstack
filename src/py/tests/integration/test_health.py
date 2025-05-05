import pytest
from httpx import AsyncClient

from app.__metadata__ import __version__


@pytest.mark.xfail(reason="Flakey connection to service sometimes causes failures.")
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200

    expected = {
        "database_status": "online",
        "app": "app",
        "version": __version__,
    }

    assert response.json() == expected
