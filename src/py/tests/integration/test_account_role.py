from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient


async def test_superuser_role_access(
    client: AsyncClient,
    user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    # user should not see all teams to start
    response = await client.get("/api/teams", headers=user_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) == 1

    # assign the role
    response = await client.post(
        "/api/roles/superuser/assign",
        json={"userName": "user@example.com"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Successfully assigned the 'superuser' role to user@example.com."
    response = await client.patch(
        "/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999",
        json={"name": "TEST UPDATE"},
        headers=user_token_headers,
    )
    assert response.status_code == 200
    # retrieve
    response = await client.get("/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_token_headers)
    assert response.status_code == 200
    response = await client.get("/api/teams", headers=user_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) == 3

    # superuser should see all
    response = await client.get("/api/teams", headers=superuser_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) == 3
    # delete
    # revoke role now
    response = await client.post(
        "/api/roles/superuser/revoke",
        json={"userName": "user@example.com"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201
    response = await client.delete("/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_token_headers)
    assert response.status_code == 403
    response = await client.delete("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=user_token_headers)
    assert response.status_code == 204

    # retrieve should now fail
    response = await client.get("/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_token_headers)
    assert response.status_code == 403
    # user should only see 1 now.
    response = await client.get("/api/teams", headers=user_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) == 0
