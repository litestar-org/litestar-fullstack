from httpx import AsyncClient


async def test_update_team(superuser_client: AsyncClient) -> None:
    response = await superuser_client.patch("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "My Team"})
    assert response.status_code == 200
    assert response.json()["name"] == "SuperTeam"
