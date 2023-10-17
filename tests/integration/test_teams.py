from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_teams_with_no_auth(client: "AsyncClient") -> None:
    response = await client.patch("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "TEST UPDATE"})
    assert response.status_code == 401
    response = await client.post(
        "/api/teams/",
        json={"name": "A User", "email": "new-user@example.com", "password": "S3cret!"},
    )
    assert response.status_code == 401
    response = await client.get("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 401
    response = await client.get("/api/teams")
    assert response.status_code == 401
    response = await client.delete("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 401


async def test_teams_with_incorrect_role(client: "AsyncClient", user_token_headers: dict[str, str]) -> None:
    response = await client.patch(
        "/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        json={"name": "TEST UPDATE"},
        headers=user_token_headers,
    )
    assert response.status_code == 403
    response = await client.post(
        "/api/teams/",
        json={"name": "A new team."},
        headers=user_token_headers,
    )
    assert response.status_code == 201
    response = await client.get("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=user_token_headers)
    assert response.status_code == 403
    response = await client.get("/api/teams", headers=user_token_headers)
    assert response.status_code == 200
    response = await client.delete("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=user_token_headers)
    assert response.status_code == 403


async def test_teams_list(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    response = await client.get("/api/teams", headers=superuser_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) > 0


async def test_teams_get(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    response = await client.get("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Assessment Team"


async def test_teams_create(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/teams/",
        json={"name": "A User", "email": "new-user@example.com", "password": "S3cret!"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201


async def test_teams_update(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    response = await client.patch(
        "/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        json={"name": "Name Changed"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200


async def test_teams_delete(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    response = await client.delete(
        "/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204
    # ensure we didn't cascade delete the users that were members of the team
    response = await client.get(
        "/api/users/6ef29f3c-3560-4d15-ba6b-a2e5c721e4d3",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
