from httpx import AsyncClient


async def test_get_team(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    response = await client.get("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["id"] == "97108ac1-ffcb-411d-8b1e-d9183399f63b"


async def test_update_team(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    response = await client.patch(
        "/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        headers=superuser_token_headers,
        json={"name": "My Team"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "My Team"
