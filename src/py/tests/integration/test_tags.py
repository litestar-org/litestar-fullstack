from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient


async def test_tags_list(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    response = await client.get("/api/tags", headers=superuser_token_headers)
    resj = response.json()
    assert response.status_code == 200
    # The seed data creates 3 unique tags ("new", "another", "extra") from the teams fixture
    # Additional tags may be created by other fixtures, so we check for at least 3
    assert int(resj["total"]) >= 3
