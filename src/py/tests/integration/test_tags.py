from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_tags_list(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    response = await client.get("/api/tags", headers=superuser_token_headers)
    resj = response.json()
    assert response.status_code == 200
    assert int(resj["total"]) == 3
