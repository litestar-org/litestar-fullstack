from httpx import AsyncClient


async def test_get_team(superuser_client: AsyncClient) -> None:
    response = await superuser_client.get("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 200
    assert response.json()["id"] == "97108ac1-ffcb-411d-8b1e-d9183399f63b"


async def test_update_team(superuser_client: AsyncClient) -> None:
    response = await superuser_client.patch("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "My Team"})
    assert response.status_code == 200
    assert response.json()["name"] == "My Team"
